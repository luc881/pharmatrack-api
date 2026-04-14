from fastapi import Depends, HTTPException, APIRouter, Request
from sqlalchemy import or_
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
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
from pharmatrack.utils.validators import (
    validate_units_schema,
    normalize_units,
    merge_product_units,
    validate_unit_name_for_sale,
)
from pharmatrack.utils.pagination import paginate
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE, LIMIT_SEARCH
from ...utils.logger import get_logger

logger = get_logger(__name__)

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# =========================================================
# GET /
# =========================================================
_ORDERING_MAP = {
    "title":          Product.title.asc(),
    "-title":         Product.title.desc(),
    "price_retail":   Product.price_retail.asc(),
    "-price_retail":  Product.price_retail.desc(),
    "price_cost":     Product.price_cost.asc(),
    "-price_cost":    Product.price_cost.desc(),
    "created_at":     Product.created_at.asc(),
    "-created_at":    Product.created_at.desc(),
}


@router.get("",
            response_model=PaginatedResponse[ProductResponse],
            summary="List all products",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
@limiter.limit(LIMIT_READ)
async def read_all(
    request: Request,
    db: db_dependency,
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    sku: str | None = None,
    brand_id: int | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    ordering: str | None = None,
):
    query = db.query(Product)

    if sku:
        query = query.filter(Product.sku == sku)
    elif search:
        query = query.filter(
            or_(Product.title.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%"))
        )

    if brand_id is not None:
        query = query.filter(Product.brand_id == brand_id)
    if category_id is not None:
        query = query.filter(Product.product_category_id == category_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    order_clause = _ORDERING_MAP.get(ordering) if ordering else None
    query = query.order_by(order_clause if order_clause is not None else Product.created_at.desc())

    return paginate(query, pagination)


# =========================================================
# GET /search
# =========================================================
@router.get("/search",
            response_model=PaginatedResponse[ProductResponse],
            summary="Search and filter products",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
@limiter.limit(LIMIT_SEARCH)
async def search_products(
    request: Request,
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


# =========================================================
# GET /{product_id}
# =========================================================
@router.get("/{product_id}",
            response_model=ProductDetailsResponse,
            summary="Get product details",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCTS)
async def read_product(product_id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


# =========================================================
# POST /
# =========================================================
@router.post("",
             response_model=ProductDetailsResponse,
             summary="Create a new product",
             status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_PRODUCTS)
@limiter.limit(LIMIT_WRITE)
async def create_product(request: Request, product: ProductCreate, db: db_dependency):
    # normalize_units modifica en-place (no retorna nada)
    normalize_units(product)
    validate_units_schema(product)
    validate_unit_name_for_sale(product)

    # Validar SKU unico
    if db.query(Product).filter(Product.sku == product.sku).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists."
        )

    # Validar slug unico
    if db.query(Product).filter(Product.slug == product.slug).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this title and SKU combination already exists."
        )

    # Validar ingredientes ANTES de crear
    if product.ingredients:
        ingredient_ids = {ing.ingredient_id for ing in product.ingredients}
        valid_ids = {
            row[0]
            for row in db.query(Ingredient.id).filter(Ingredient.id.in_(ingredient_ids)).all()
        }
        missing = ingredient_ids - valid_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient not found: {list(missing)}"
            )

    # slug tiene Field(exclude=True) -> hay que inyectarlo manualmente
    slug = product.slug
    product_data = product.model_dump(mode="json", exclude={"ingredients"}, exclude_none=True)
    product_data["slug"] = slug

    new_product = Product(**product_data)
    db.add(new_product)
    db.flush()

    if product.ingredients:
        db.add_all([
            ProductHasIngredient(
                product_id=new_product.id,
                ingredient_id=ing.ingredient_id,
                amount=ing.amount,
            )
            for ing in product.ingredients
        ])

    db.commit()
    db.refresh(new_product)
    logger.info("Product created id=%s title=%s sku=%s", new_product.id, new_product.title, new_product.sku)
    return new_product


# =========================================================
# PUT /{product_id}
# =========================================================
@router.put("/{product_id}",
            response_model=ProductDetailsResponse,
            summary="Update a product",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_PRODUCTS)
async def update_product(product_id: int, product_request: ProductUpdate, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # Validar unidades (estado final fusionado)
    merged = merge_product_units(product, product_request)
    normalize_units(merged)
    validate_units_schema(merged)
    validate_unit_name_for_sale(merged)

    # Validar SKU duplicado
    if product_request.sku and product_request.sku != product.sku:
        if db.query(Product).filter(Product.sku == product_request.sku).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this SKU already exists."
            )

    # Recalcular slug si cambia title o sku
    if product_request.title is not None or product_request.sku is not None:
        final_title = product_request.title or product.title
        final_sku = product_request.sku if product_request.sku is not None else product.sku
        new_slug = _product_slug(final_title, final_sku)
        if new_slug != product.slug:
            if db.query(Product).filter(Product.slug == new_slug, Product.id != product_id).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A product with this title and SKU combination already exists."
                )
            product_request.slug = new_slug

    # Validar ingredientes ANTES de modificar nada
    if product_request.ingredients is not None:
        ingredient_ids = {ing.ingredient_id for ing in product_request.ingredients}
        valid_ids = {
            row[0]
            for row in db.query(Ingredient.id).filter(Ingredient.id.in_(ingredient_ids)).all()
        }
        missing = ingredient_ids - valid_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient not found: {list(missing)}"
            )

    update_data = product_request.model_dump(
        mode="json",
        exclude={"ingredients"},
        exclude_unset=True,
    )
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
                amount=ing.amount,
            )
            for ing in product_request.ingredients
        ])

    try:
        db.commit()
        db.refresh(product)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Error updating product id=%s: %s", product_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update product.")

    logger.info("Product updated id=%s", product_id)
    return product


# =========================================================
# PATCH /{product_id}/toggle-active
# =========================================================
@router.patch("/{product_id}/toggle-active",
              response_model=ProductDetailsResponse,
              summary="Toggle product availability",
              dependencies=CAN_UPDATE_PRODUCTS)
async def toggle_product_active(product_id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    logger.info("Product id=%s toggled is_active=%s", product_id, product.is_active)
    return product


# =========================================================
# DELETE /{product_id}
# =========================================================
@router.delete("/{product_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a product",
               dependencies=CAN_DELETE_PRODUCTS)
@limiter.limit(LIMIT_WRITE)
async def delete_product(request: Request, product_id: int, db: db_dependency):
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if not existing_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    db.delete(existing_product)
    db.commit()
    logger.info("Product deleted id=%s", product_id)
    return None