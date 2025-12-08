from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...utils.permissions import CAN_READ_PRODUCT_MASTERS, CAN_CREATE_PRODUCT_MASTERS, CAN_UPDATE_PRODUCT_MASTERS, CAN_DELETE_PRODUCT_MASTERS
from ...models.product_master.orm import ProductMaster
from ...models.product_master.schemas import ProductMasterCreate, ProductMasterResponse, ProductMasterUpdate
from ...models.product_categories.orm import ProductCategory

db_dependency = Annotated[Session, Depends(get_db)]


router = APIRouter(
    prefix="/productsmaster",
    tags=["Products Master"]
)

@router.get("/",
            response_model=list[ProductMasterResponse],
            summary="List all product masters",
            description="Retrieve all product masters currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_MASTERS)
async def read_all(db: db_dependency):
    product_masters = db.query(ProductMaster).all()
    return product_masters

@router.post(
    "/",
    response_model=ProductMasterResponse,
    summary="Create a new product master",
    description="Creates a new Product Master record in the database.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PRODUCT_MASTERS
)
async def create_product_master(
    payload: ProductMasterCreate,
    db: db_dependency
):
    # --------------------------------------------
    # 🔍 Validar si ya existe un master con el mismo nombre (opcional)
    # --------------------------------------------
    existing = db.query(ProductMaster).filter(
        ProductMaster.name.ilike(payload.name)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product master with name '{payload.name}' already exists."
        )

    # --------------------------------------------
    # 🔍 Validar que la categoría exista
    # --------------------------------------------
    category = db.query(ProductCategory).filter(
        ProductCategory.id == payload.product_category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category {payload.product_category_id} does not exist."
        )

    # --------------------------------------------
    # 🟢 Crear el registro
    # --------------------------------------------
    new_master = ProductMaster(
        name=payload.name,
        description=payload.description,
        product_category_id=payload.product_category_id
    )

    db.add(new_master)
    db.commit()
    db.refresh(new_master)

    return new_master
