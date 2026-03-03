from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db
from ...models.purchase_details.orm import PurchaseDetail
from ...models.purchase_details.schemas import (
    PurchaseDetailCreate,
    PurchaseDetailUpdate,
    PurchaseDetailResponse,
)
from ...models.purchases.orm import Purchase
from ...models.products.orm import Product
from ...utils.permissions import (
    CAN_READ_PURCHASE_DETAILS,
    CAN_CREATE_PURCHASE_DETAILS,
    CAN_UPDATE_PURCHASE_DETAILS,
    CAN_DELETE_PURCHASE_DETAILS,
)

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/purchase-details", tags=["Purchase Details"])


# ------------------------------------------------------------------
# GET ALL
# ------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[PurchaseDetailResponse],
    summary="List all purchase details",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PURCHASE_DETAILS,
)
async def read_all(db: db_dependency):
    return db.query(PurchaseDetail).all()


# ------------------------------------------------------------------
# GET BY ID
# ------------------------------------------------------------------
@router.get(
    "/{detail_id}",
    response_model=PurchaseDetailResponse,
    summary="Get a purchase detail by ID",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PURCHASE_DETAILS,
)
async def read_one(detail_id: int, db: db_dependency):
    detail = db.get(PurchaseDetail, detail_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase detail not found"
        )
    return detail


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
@router.post(
    "/",
    response_model=PurchaseDetailResponse,
    summary="Create a new purchase detail",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PURCHASE_DETAILS,
)
async def create(payload: PurchaseDetailCreate, db: db_dependency):
    if not db.get(Purchase, payload.purchase_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found"
        )
    if not db.get(Product, payload.product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    detail = PurchaseDetail(**payload.model_dump())
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
@router.put(
    "/{detail_id}",
    response_model=PurchaseDetailResponse,
    summary="Update a purchase detail",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PURCHASE_DETAILS,
)
async def update(detail_id: int, payload: PurchaseDetailUpdate, db: db_dependency):
    detail = db.get(PurchaseDetail, detail_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase detail not found"
        )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(detail, key, value)

    db.commit()
    db.refresh(detail)
    return detail


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
@router.delete(
    "/{detail_id}",
    summary="Delete a purchase detail",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=CAN_DELETE_PURCHASE_DETAILS,
)
async def delete(detail_id: int, db: db_dependency):
    detail = db.get(PurchaseDetail, detail_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase detail not found"
        )
    db.delete(detail)
    db.commit()