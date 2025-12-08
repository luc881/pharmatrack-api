from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...models.products.orm import Product
from ...models.products.schemas import ProductCreate, ProductResponse, ProductUpdate, ProductSearchParams, ProductDetailsResponse
from ...utils.permissions import CAN_READ_PRODUCTS, CAN_CREATE_PRODUCTS, CAN_UPDATE_PRODUCTS, CAN_DELETE_PRODUCTS
from possystem.models.product_has_ingredients.orm import ProductHasIngredient
from possystem.models.ingredients.orm import Ingredient


db_dependency = Annotated[Session, Depends(get_db)]


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.get("/",
            response_model=list[ProductResponse],
            summary="List all products",
            description="Retrieve all products currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
async def read_all(db: db_dependency):
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return products

@router.get("/search",
            response_model=list[ProductResponse],
            summary="Search and filter products",
            description="Search products by title, or availability.",
            dependencies=CAN_READ_PRODUCTS)
async def search_products(db: db_dependency, params: ProductSearchParams = Depends()):
    query = db.query(Product)

    if params.title:
        query = query.filter(Product.title.ilike(f"%{params.title}%"))
    if params.is_active is not None:
        query = query.filter(Product.is_active == params.is_active)

    products = query.all()
    return products

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

    # 1. Validar SKU duplicado
    if db.query(Product).filter(Product.sku == product_request.sku).first():
        raise HTTPException(
            status_code=400,
            detail="Product with this SKU already exists."
        )

    # 2. Crear producto base
    product_model = Product(
        **product_request.model_dump(
            mode="json",
            exclude={"ingredients"},
            exclude_none=True
        )
    )
    db.add(product_model)
    db.commit()
    db.refresh(product_model)

    # 3. Ingredientes
    if product_request.ingredients:

        # Deduplicar (pythonico)
        unique_ingredients = {
            ing.ingredient_id: ing
            for ing in product_request.ingredients
        }

        # Validar existencia
        ingredient_ids = list(unique_ingredients.keys())

        valid_ids = {
            row[0]
            for row in db.query(Ingredient.id).filter(
                Ingredient.id.in_(ingredient_ids)
            ).all()
        }

        missing = [i for i in ingredient_ids if i not in valid_ids]
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient not found: {missing}"
            )

        # Insertar todos de una vez
        db.add_all([
            ProductHasIngredient(
                product_id=product_model.id,
                ingredient_id=ing_id,
                amount=unique_ingredients[ing_id].amount
            )
            for ing_id in unique_ingredients
        ])

    db.commit()
    db.refresh(product_model)

    return product_model



@router.put(
    "/{product_id}",
    response_model=ProductDetailsResponse,
    summary="Update an existing product",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PRODUCTS
)
async def update_product(product_id: int, product_request: ProductUpdate, db: db_dependency):

    # 1. Verificar que exista el producto
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    # 2. Validar que el SKU no esté duplicado (si viene y cambió)
    if product_request.sku and product_request.sku != product.sku:
        if db.query(Product).filter(Product.sku == product_request.sku).first():
            raise HTTPException(
                status_code=400,
                detail="Product with this SKU already exists."
            )

    # 3. Actualizar campos simples del modelo
    update_data = product_request.model_dump(
        mode="json",
        exclude={"ingredients"},
        exclude_unset=True
    )
    for key, value in update_data.items():
        setattr(product, key, value)

    # 4. Actualizar ingredientes si vienen en la petición
    if product_request.ingredients is not None:

        # 4.1 Deduplicar ingredientes (igual que en POST)
        unique_ingredients = {
            ing.ingredient_id: ing
            for ing in product_request.ingredients
        }

        ingredient_ids = list(unique_ingredients.keys())

        # 4.2 Validar existencia de ingredientes masivamente
        valid_ids = {
            row[0]
            for row in db.query(Ingredient.id).filter(
                Ingredient.id.in_(ingredient_ids)
            ).all()
        }

        missing = [i for i in ingredient_ids if i not in valid_ids]
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient not found: {missing}"
            )

        # 4.3 Borrar ingredientes actuales
        db.query(ProductHasIngredient).filter(
            ProductHasIngredient.product_id == product.id
        ).delete()

        # 4.4 Insertar todos de una vez
        db.add_all([
            ProductHasIngredient(
                product_id=product.id,
                ingredient_id=ing_id,
                amount=unique_ingredients[ing_id].amount
            )
            for ing_id in unique_ingredients
        ])

    # Guardar cambios
    db.commit()
    db.refresh(product)

    return product




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
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    db.delete(existing_product)
    db.commit()
