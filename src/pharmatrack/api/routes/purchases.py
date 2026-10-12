from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db, db_dependency
from ...models.purchases.orm import Purchase
from ...models.purchase_details.orm import PurchaseDetail
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
from ...utils.purchase_stock import stock_in, stock_out
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE


router = APIRouter(prefix="/purchases", tags=["Purchases"])


def _add_items(db, purchase, items):
    """Crea los renglones y suma cada uno al stock."""
    for item in items:
        detail = PurchaseDetail(**item.model_dump())
        purchase.details.append(detail)
        stock_in(db, detail)


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

    purchase = Purchase(**payload.model_dump(exclude={"items"}, exclude_none=True))
    db.add(purchase)
    _add_items(db, purchase, payload.items)
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

    data = payload.model_dump(exclude_unset=True, exclude={"items"})

    if "supplier_id" in data and not db.get(Supplier, data["supplier_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    if "user_id" in data and not db.get(User, data["user_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for key, value in data.items():
        setattr(purchase, key, value)

    if payload.items is not None:
        stock_out(db, purchase.details)
        purchase.details.clear()
        db.flush()
        _add_items(db, purchase, payload.items)

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
    stock_out(db, purchase.details)
    db.delete(purchase)
    db.commit()