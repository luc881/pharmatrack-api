from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...db.session import get_db
from starlette import status
from ...utils.permissions import CAN_READ_PRODUCT_BRANDS, CAN_CREATE_PRODUCT_BRANDS, CAN_UPDATE_PRODUCT_BRANDS, CAN_DELETE_PRODUCT_BRANDS
from ...models.product_brand.orm import ProductBrand
from ...models.product_brand.schemas import (
    ProductBrandCreate,
    ProductBrandResponse,
    ProductBrandUpdate,
    ProductBrandSearchParams,
    ProductBrandDetailsResponse,
    PaginatedResponse,
    PaginationParams,
)
from ...models.products.orm import Product
from pharmatrack.utils.pagination import paginate

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/productsbrand",
    tags=["Products Brand"]
)


@router.get("",
            response_model=PaginatedResponse[ProductBrandResponse],
            summary="List all product brands",
            description="Retrieve all product brands currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_BRANDS)
async def read_all(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(ProductBrand).order_by(ProductBrand.name.asc())
    return paginate(query, pagination)


@router.get("/search",
            response_model=PaginatedResponse[ProductBrandDetailsResponse],
            summary="Search product brands with filters",
            description="Advanced filtering of product brands, including product attributes.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_BRANDS)
async def search_brands(
    db: db_dependency,
    params: ProductBrandSearchParams = Depends(),
    pagination: PaginationParams = Depends()
):
    query = db.query(ProductBrand)

    if params.name:
        query = query.filter(ProductBrand.name.ilike(f"%{params.name}%"))

    if params.has_logo is not None:
        if params.has_logo:
            query = query.filter(ProductBrand.logo.isnot(None))
        else:
            query = query.filter(ProductBrand.logo.is_(None))

    if params.is_active is not None:
        query = query.join(ProductBrand.products).filter(
            Product.is_active == params.is_active
        )

    if params.product_title:
        query = query.join(ProductBrand.products).filter(
            Product.title.ilike(f"%{params.product_title}%")
        )

    if params.min_products is not None:
        query = (
            query.join(ProductBrand.products)
                 .group_by(ProductBrand.id)
                 .having(func.count(Product.id) >= params.min_products)
        )

    # distinct() para evitar duplicados por los joins
    return paginate(query.distinct(), pagination)


@router.get("/{brand_id}",
            response_model=ProductBrandResponse,
            summary="Get a product brand by ID",
            description="Retrieve a product brand using its ID.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_BRANDS)
async def read_brand(brand_id: int, db: db_dependency):
    brand = db.query(ProductBrand).filter(ProductBrand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found."
        )
    return brand


@router.post("",
             response_model=ProductBrandResponse,
             summary="Create a new product brand",
             description="Create a new product brand using the provided data.",
             status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_PRODUCT_BRANDS)
async def create_brand(payload: ProductBrandCreate, db: db_dependency):
    existing = db.query(ProductBrand).filter(
        ProductBrand.slug == payload.slug
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The brand '{payload.name}' already exists."
        )

    # Inyectar slug explícitamente — model_dump() lo excluye por exclude=True
    data = payload.model_dump()
    data["slug"] = payload.slug
    new_brand = ProductBrand(**data)
    db.add(new_brand)
    db.commit()
    db.refresh(new_brand)
    return new_brand


@router.put("/{brand_id}",
            response_model=ProductBrandResponse,
            summary="Update a product brand",
            description="Update an existing product brand with the provided data.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_PRODUCT_BRANDS)
async def update_brand(brand_id: int, payload: ProductBrandUpdate, db: db_dependency):
    brand = db.query(ProductBrand).filter(ProductBrand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found."
        )

    if payload.slug and payload.slug != brand.slug:
        existing = db.query(ProductBrand).filter(
            ProductBrand.slug == payload.slug,
            ProductBrand.id != brand_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The brand name '{payload.name}' is already in use."
            )

    # Inyectar slug si el nombre cambió
    data = payload.model_dump(exclude_unset=True)
    if payload.slug is not None:
        data["slug"] = payload.slug
    for field, value in data.items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/{brand_id}",
               summary="Delete a product brand",
               description="Remove a product brand from the database.",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=CAN_DELETE_PRODUCT_BRANDS)
async def delete_brand(brand_id: int, db: db_dependency):
    brand = db.query(ProductBrand).filter(ProductBrand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found."
        )

    db.delete(brand)
    db.commit()
    return None