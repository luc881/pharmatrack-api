from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from datetime import datetime, timezone

from ...models.suppliers.orm import Supplier
from ...models.suppliers.schemas import SupplierCreate, SupplierResponse, SupplierUpdate
from ...utils.permissions import CAN_READ_SUPPLIERS, CAN_CREATE_SUPPLIERS, CAN_UPDATE_SUPPLIERS, CAN_DELETE_SUPPLIERS

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)

@router.get(
    "/",
    response_model=list[SupplierResponse],
    summary="List all suppliers",
    description="Retrieve all suppliers currently stored in the database.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SUPPLIERS
)
async def read_all(db: db_dependency):
    suppliers = db.query(Supplier).all()
    return suppliers

@router.post(
    "/",
    response_model=SupplierResponse,
    summary="Create a new supplier",
    description="Create a new supplier with the provided details.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SUPPLIERS
)
async def create(supplier: SupplierCreate, db: db_dependency):
    # Check for unique constraints (e.g., email, ruc)
    if supplier.email:
        existing_email = db.query(Supplier).filter(Supplier.email == supplier.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
    if supplier.ruc:
        existing_ruc = db.query(Supplier).filter(Supplier.ruc == supplier.ruc).first()
        if existing_ruc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RUC already in use")
    new_supplier = Supplier(**supplier.model_dump())
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier

@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update an existing supplier",
    description="Update the details of an existing supplier by its ID.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SUPPLIERS
)
async def update(supplier_id: int, supplier: SupplierUpdate, db: db_dependency):
    existing_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not existing_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    # Check for unique constraints (e.g., email, ruc) if they are being updated
    if supplier.email and supplier.email != existing_supplier.email:
        existing_email = db.query(Supplier).filter(Supplier.email == supplier.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
    if supplier.ruc and supplier.ruc != existing_supplier.ruc:
        existing_ruc = db.query(Supplier).filter(Supplier.ruc == supplier.ruc).first()
        if existing_ruc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RUC already in use")

    for key, value in supplier.model_dump(exclude_unset=True).items():
        setattr(existing_supplier, key, value)
    existing_supplier.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(existing_supplier)
    return existing_supplier


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a supplier",
    description="Delete an existing supplier by its ID.",
    dependencies=CAN_DELETE_SUPPLIERS
)
async def delete(supplier_id: int, db: db_dependency):
    existing_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not existing_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    db.delete(existing_supplier)
    db.commit()
    return