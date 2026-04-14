from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db
from ...models.suppliers.orm import Supplier
from ...models.suppliers.schemas import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
    PaginatedResponse,
    PaginationParams,
)
from ...utils.permissions import (
    CAN_READ_SUPPLIERS,
    CAN_CREATE_SUPPLIERS,
    CAN_UPDATE_SUPPLIERS,
    CAN_DELETE_SUPPLIERS,
)
from pharmatrack.utils.pagination import paginate
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


# ------------------------------------------------------------------
# GET ALL
# ------------------------------------------------------------------
@router.get(
    "",
    response_model=PaginatedResponse[SupplierResponse],
    summary="List all suppliers",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SUPPLIERS,
)
@limiter.limit(LIMIT_READ)
async def read_all(request: Request, db: db_dependency, pagination: PaginationParams = Depends()):
    return paginate(db.query(Supplier).order_by(Supplier.id.asc()), pagination)


# ------------------------------------------------------------------
# GET BY ID
# ------------------------------------------------------------------
@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get a supplier by ID",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SUPPLIERS,
)
async def read_one(supplier_id: int, db: db_dependency):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
@router.post(
    "",
    response_model=SupplierResponse,
    summary="Create a new supplier",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SUPPLIERS,
)
@limiter.limit(LIMIT_WRITE)
async def create(request: Request, payload: SupplierCreate, db: db_dependency):
    if payload.email:
        if db.query(Supplier).filter(Supplier.email == payload.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
    if payload.rfc:
        if db.query(Supplier).filter(Supplier.rfc == payload.rfc).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="RFC already in use"
            )

    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update an existing supplier",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SUPPLIERS,
)
@limiter.limit(LIMIT_WRITE)
async def update(request: Request, supplier_id: int, payload: SupplierUpdate, db: db_dependency):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    if payload.email and payload.email != supplier.email:
        if db.query(Supplier).filter(Supplier.email == payload.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
    if payload.rfc and payload.rfc != supplier.rfc:
        if db.query(Supplier).filter(Supplier.rfc == payload.rfc).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="RFC already in use"
            )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)

    db.commit()
    db.refresh(supplier)
    return supplier


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
@router.delete(
    "/{supplier_id}",
    summary="Delete a supplier",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=CAN_DELETE_SUPPLIERS,
)
async def delete(supplier_id: int, db: db_dependency):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    db.delete(supplier)
    db.commit()