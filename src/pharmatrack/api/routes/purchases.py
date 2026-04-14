from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db
from ...models.purchases.orm import Purchase
from ...models.purchases.schemas import (
    PurchaseCreate,
    PurchaseResponse,
    PurchaseUpdate,
    PaginatedResponse,
    PaginationParams,
)
from ...models.suppliers.orm import Supplier
from ...models.users.orm import User
from ...utils.permissions import (
    CAN_READ_PURCHASES,
    CAN_CREATE_PURCHASES,
    CAN_UPDATE_PURCHASES,
    CAN_DELETE_PURCHASES,
)
from pharmatrack.utils.pagination import paginate
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/purchases", tags=["Purchases"])


# ------------------------------------------------------------------
# GET ALL
# ------------------------------------------------------------------
@router.get(
    "",
    response_model=PaginatedResponse[PurchaseResponse],
    summary="List all purchases",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PURCHASES,
)
@limiter.limit(LIMIT_READ)
async def read_all(request: Request, db: db_dependency, pagination: PaginationParams = Depends()):
    return paginate(db.query(Purchase).order_by(Purchase.id.desc()), pagination)


# ------------------------------------------------------------------
# GET BY ID
# ------------------------------------------------------------------
@router.get(
    "/{purchase_id}",
    response_model=PurchaseResponse,
    summary="Get a purchase by ID",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PURCHASES,
)
async def read_one(purchase_id: int, db: db_dependency):
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    return purchase


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
@router.post(
    "",
    response_model=PurchaseResponse,
    summary="Create a new purchase",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PURCHASES,
)
@limiter.limit(LIMIT_WRITE)
async def create(request: Request, payload: PurchaseCreate, db: db_dependency):
    if not db.get(Supplier, payload.supplier_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    purchase = Purchase(**payload.model_dump())
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
@router.put(
    "/{purchase_id}",
    response_model=PurchaseResponse,
    summary="Update an existing purchase",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PURCHASES,
)
@limiter.limit(LIMIT_WRITE)
async def update(request: Request, purchase_id: int, payload: PurchaseUpdate, db: db_dependency):
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")

    data = payload.model_dump(exclude_unset=True)

    if "supplier_id" in data and not db.get(Supplier, data["supplier_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    if "user_id" in data and not db.get(User, data["user_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for key, value in data.items():
        setattr(purchase, key, value)

    db.commit()
    db.refresh(purchase)
    return purchase


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
@router.delete(
    "/{purchase_id}",
    summary="Delete a purchase",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=CAN_DELETE_PURCHASES,
)
async def delete(purchase_id: int, db: db_dependency):
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    db.delete(purchase)
    db.commit()