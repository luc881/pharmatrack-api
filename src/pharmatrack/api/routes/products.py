from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...models.products.orm import Product
from ...models.products.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductSearchParams,
    ProductDetailsResponse,
    PaginationParams,
    PaginatedResponse,
    _product_slug,
)
from ...utils.permissions import CAN_READ_PRODUCTS, CAN_CREATE_PRODUCTS, CAN_UPDATE_PRODUCTS, CAN_DELETE_PRODUCTS
from pharmatrack.models.product_has_ingredients.orm import ProductHasIngredient
from pharmatrack.models.ingredients.orm import Ingredient
from sqlalchemy.exc import SQLAlchemyError
from pharmatrack.utils.validators import validate_units_schema, merge_product_units, validate_unit_name_for_sale, \
    normalize_units
from pharmatrack.utils.pagination import paginate

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("/",
            response_model=PaginatedResponse[ProductResponse],
            summary="List all products",
            description="Retrieve all products currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
async def read_all(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(Product).order_by(Product.created_at.desc())
    return paginate(query, pagination)


@router.get("/search",
            response_model=PaginatedResponse[ProductResponse],
            summary="Search and filter products",
            description="Search products by title, or availability.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
async def search_products(
        db: db_dependency,
        params: ProductSearchParams = Depends(),
        pagination: PaginationParams = Depends()
):
    query = db.query(Product)

    if params.title:
        query = query.filter(Product.title.ilike(f"%{params.title}%"))
    if params.is_active is not None:
        query = query.filter(Product.is_active == params.is_active)
    if params.is_unit_sale is not None:
        query = query.filter(Product.is_unit_sale == params.is_unit_sale)
    if params.brand_id is not None:
        query = query.filter(Product.brand_id == params.brand_id)
    if params.product_master_id is not None:
        query = query.filter(Product.product_master_id == params.product_master_id)

    return paginate(query, pagination)


@router.get("/{product_id}",
            response_model=ProductDetailsResponse,
            summary="Get product details",
            description="Retrieve detailed information about a specific product by its ID.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
async def read_product(product_id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    return product


@router.post(
    "/",
    response_model=ProductDetailsResponse,
    summary="Create a new product",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PRODUCTS
)
async def create_product(product_request: ProductCreate, db: db_dependency):
    # 🔹 VALIDACIÓN DE UNIDADES
    normalize_units(product_request)
    validate_units_schema(product_request)
    validate_unit_name_for_sale(product_request)

    # 1. Validar SKU
    if db.query(Product).filter(Product.sku == product_request.sku).first():
        raise HTTPException(status_code=400, detail="Product with this SKU already exists.")

    # 2. Validar slug único
    if db.query(Product).filter(Product.slug == product_request.slug).first():
        raise HTTPException(
            status_code=400,
            detail="A product with this title and SKU combination already exists."
        )

    # 3. Validar marca
    if product_request.brand_id:
        if not db.query(Product).filter(Product.id == product_request.brand_id).first():
            raise HTTPException(status_code=404, detail="Brand not found.")

    # 4. Validar ingredientes ANTES
    if product_request.ingredients:
        ingredient_ids = {ing.ingredient_id for ing in product_request.ingredients}

        valid_ids = {
            row[0]
            for row in db.query(Ingredient.id).filter(
                Ingredient.id.in_(ingredient_ids)
            ).all()
        }

        missing = ingredient_ids - valid_ids
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient not found: {list(missing)}"
            )

    # 5. Validar Product Master si se provee
    if product_request.product_master_id:
        if not db.query(Product).filter(Product.id == product_request.product_master_id).first():
            raise HTTPException(status_code=404, detail="Product Master not found.")

    # 6. Crear producto (ya todo validado)
    # ✅ FIX: slug tiene Field(exclude=True) → model_dump lo omite aunque exista.
    #    Extraerlo explícitamente y añadirlo al dict antes de construir el ORM.
    slug = product_request.slug  # generado por @model_validator, pero excluido de model_dump
    product_data = product_request.model_dump(
        mode="json",
        exclude={"ingredients"},
        exclude_none=True,
    )
    product_data["slug"] = slug  # inyectar slug manualmente

    product_model = Product(**product_data)

    db.add(product_model)
    db.flush()  # obtiene ID sin commit

    # 7. Insertar ingredientes
    if product_request.ingredients:
        db.add_all([
            ProductHasIngredient(
                product_id=product_model.id,
                ingredient_id=ing.ingredient_id,
                amount=ing.amount
            )
            for ing in product_request.ingredients
        ])

    db.commit()
    db.refresh(product_model)
    return product_model


@router.put(
    "/{product_id}",
    response_model=ProductDetailsResponse,
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PRODUCTS
)
async def update_product(product_id: int, product_request: ProductUpdate, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # 🔹 VALIDAR UNIDADES (estado final)
    merged = merge_product_units(product, product_request)
    normalize_units(merged)
    validate_units_schema(merged)
    validate_unit_name_for_sale(merged)

    # Validar SKU
    if product_request.sku and product_request.sku != product.sku:
        if db.query(Product).filter(Product.sku == product_request.sku).first():
            raise HTTPException(status_code=400, detail="Product with this SKU already exists.")

    # Validar slug: si cambió title o sku, recalcular con los valores finales y verificar unicidad
    if product_request.title is not None or product_request.sku is not None:
        final_title = product_request.title or product.title
        final_sku = product_request.sku if product_request.sku is not None else product.sku
        new_slug = _product_slug(final_title, final_sku)

        if new_slug != product.slug:
            if db.query(Product).filter(
                Product.slug == new_slug,
                Product.id != product_id
            ).first():
                raise HTTPException(
                    status_code=400,
                    detail="A product with this title and SKU combination already exists."
                )
            # Asignar el slug recalculado al request para que se persista
            product_request.slug = new_slug

    # Validar marca
    if product_request.brand_id:
        if not db.query(Product).filter(Product.id == product_request.brand_id).first():
            raise HTTPException(status_code=404, detail="Brand not found.")

    # Validar Product Master si se provee
    if product_request.product_master_id:
        if not db.query(Product).filter(Product.id == product_request.product_master_id).first():
            raise HTTPException(status_code=404, detail="Product Master not found.")

    # Validar ingredientes ANTES de modificar nada
    if product_request.ingredients is not None:
        ingredient_ids = {ing.ingredient_id for ing in product_request.ingredients}

        valid_ids = {
            row[0]
            for row in db.query(Ingredient.id).filter(
                Ingredient.id.in_(ingredient_ids)
            ).all()
        }

        missing = ingredient_ids - valid_ids
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient not found: {list(missing)}"
            )

    # ✅ FIX: with db.begin() falla porque SQLAlchemy ya tiene una transacción activa.
    #    Aplicar cambios directamente y llamar db.commit().
    # ✅ FIX: slug tiene Field(exclude=True) → model_dump(exclude_unset=True) lo omite.
    #    Extraerlo explícitamente si fue recalculado arriba.
    update_data = product_request.model_dump(
        mode="json",
        exclude={"ingredients"},
        exclude_unset=True,
    )
    # Si el slug fue recalculado arriba (product_request.slug = new_slug), inyectarlo
    if product_request.slug is not None:
        update_data["slug"] = product_request.slug

    for key, value in update_data.items():
        setattr(product, key, value)

    if product_request.ingredients is not None:
        db.query(ProductHasIngredient).filter(
            ProductHasIngredient.product_id == product.id
        ).delete()

        db.add_all([
            ProductHasIngredient(
                product_id=product.id,
                ingredient_id=ing.ingredient_id,
                amount=ing.amount
            )
            for ing in product_request.ingredients
        ])

    try:
        db.commit()
        db.refresh(product)
        return product
    except SQLAlchemyError:
        db.rollback()
        raise


@router.patch("/{product_id}/toggle-active",
              response_model=ProductResponse,
              summary="Toggle product availability",
              description="Activate or deactivate a product quickly.",
              dependencies=CAN_UPDATE_PRODUCTS)
async def toggle_product_active(product_id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}",
               summary="Delete a product",
               description="Delete a product by its ID.",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=CAN_DELETE_PRODUCTS)
async def delete_product(product_id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    db.delete(product)
    db.commit()
    return None