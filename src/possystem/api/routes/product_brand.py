from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...utils.permissions import CAN_READ_PRODUCT_BRANDS, CAN_CREATE_PRODUCT_BRANDS, CAN_UPDATE_PRODUCT_BRANDS, CAN_DELETE_PRODUCT_BRANDS
from ...models.product_brand.orm import ProductBrand
from ...models.product_brand.schemas import ProductBrandCreate, ProductBrandResponse, ProductBrandUpdate

db_dependency = Annotated[Session, Depends(get_db)]


router = APIRouter(
    prefix="/productsbrand",
    tags=["Products Brand"]
)

@router.get("/",
            response_model=list[ProductBrandResponse],
            summary="List all product brands",
            description="Retrieve all product brands currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_BRANDS)
async def read_all(db: db_dependency):
    product_brands = db.query(ProductBrand).all()
    return product_brands

@router.post("/",
             response_model=ProductBrandResponse,
             summary="Create a new product brand",
             description="Create a new product brand using the provided data.",
             status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_PRODUCT_BRANDS)
async def create_brand(payload: ProductBrandCreate, db: db_dependency):
    # Check if brand name already exists
    existing_brand = db.query(ProductBrand).filter(
        ProductBrand.name == payload.name
    ).first()

    if existing_brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The brand '{payload.name}' already exists."
        )

    # Create the new brand
    new_brand = ProductBrand(
        name=payload.name,
        logo=payload.logo
    )

    db.add(new_brand)
    db.commit()
    db.refresh(new_brand)

    return new_brand
