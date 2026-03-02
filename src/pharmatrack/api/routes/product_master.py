from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...utils.permissions import (
    CAN_READ_PRODUCT_MASTERS,
    CAN_CREATE_PRODUCT_MASTERS,
    CAN_UPDATE_PRODUCT_MASTERS,
    CAN_DELETE_PRODUCT_MASTERS,
)
from ...models.product_master.orm import ProductMaster
from ...models.product_master.schemas import (
    ProductMasterCreate,
    ProductMasterResponse,
    ProductMasterUpdate,
    PaginatedResponse,
    PaginationParams,
)
from pharmatrack.utils.pagination import paginate

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/productsmaster",
    tags=["Products Master"]
)


@router.get("/",
            response_model=PaginatedResponse[ProductMasterResponse],
            summary="List all product masters",
            description="Retrieve all product masters currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_MASTERS)
async def read_all(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(ProductMaster).order_by(ProductMaster.name.asc())
    return paginate(query, pagination)


@router.get("/{master_id}",
            response_model=ProductMasterResponse,
            summary="Retrieve a product master by ID",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_MASTERS)
async def read_product_master(master_id: int, db: db_dependency):
    master = db.query(ProductMaster).filter(ProductMaster.id == master_id).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product master {master_id} not found."
        )
    return master


@router.post("/",
             response_model=ProductMasterResponse,
             summary="Create a new product master",
             status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_PRODUCT_MASTERS)
async def create_product_master(payload: ProductMasterCreate, db: db_dependency):
    # Duplicate check via slug (handles case and accent variants)
    existing = db.query(ProductMaster).filter(
        ProductMaster.slug == payload.slug
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product master with name '{payload.name}' already exists."
        )

    # Inyectar slug explícitamente — model_dump() lo excluye por exclude=True
    data = payload.model_dump()
    data["slug"] = payload.slug
    new_master = ProductMaster(**data)
    db.add(new_master)
    db.commit()
    db.refresh(new_master)
    return new_master


@router.put("/{master_id}",
            response_model=ProductMasterResponse,
            summary="Update an existing product master",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_PRODUCT_MASTERS)
async def update_product_master(master_id: int, payload: ProductMasterUpdate, db: db_dependency):
    master = db.query(ProductMaster).filter(ProductMaster.id == master_id).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product master {master_id} not found."
        )

    # If name changed, verify slug is not taken by another record
    if payload.slug and payload.slug != master.slug:
        duplicate = db.query(ProductMaster).filter(
            ProductMaster.slug == payload.slug,
            ProductMaster.id != master_id
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another product master with name '{payload.name}' already exists."
            )

    # Inyectar slug si el nombre cambió
    data = payload.model_dump(exclude_unset=True)
    if payload.slug is not None:
        data["slug"] = payload.slug
    for key, value in data.items():
        setattr(master, key, value)

    db.commit()
    db.refresh(master)
    return master


@router.delete("/{master_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a product master",
               description="Deletes a product master by ID. Fails if products depend on it.",
               dependencies=CAN_DELETE_PRODUCT_MASTERS)
async def delete_product_master(master_id: int, db: db_dependency):
    master = db.query(ProductMaster).filter(ProductMaster.id == master_id).first()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product master {master_id} not found."
        )

    try:
        db.delete(master)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete product master because related products exist."
        )

    return None