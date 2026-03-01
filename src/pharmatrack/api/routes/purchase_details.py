from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from datetime import datetime, timezone

from ...models.purchase_details.orm import PurchaseDetail
from ...models.purchase_details.schemas import PurchaseDetailCreate, PurchaseDetailUpdate, PurchaseDetailResponse
from ...utils.permissions import CAN_READ_PURCHASE_DETAILS, CAN_CREATE_PURCHASE_DETAILS, CAN_UPDATE_PURCHASE_DETAILS, CAN_DELETE_PURCHASE_DETAILS

from ...models.purchases.orm import Purchase
from ...models.products.orm import Product


db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/purchasedetails",
    tags=["Purchase Details"]
)

@router.get(
    "/",
    response_model=list[PurchaseDetailResponse],
    summary="List all purchase details",
    description="Retrieve all purchase details currently stored in the database.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PURCHASE_DETAILS
)
async def read_all(db: db_dependency):
    purchase_details = db.query(PurchaseDetail).all()
    return purchase_details


@router.post(
    "/",
    response_model=PurchaseDetailResponse,
    summary="Create a new purchase detail",
    description="Create a new purchase detail with the provided information.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PURCHASE_DETAILS
)
async def create(purchase_detail: PurchaseDetailCreate, db: db_dependency):
    # Check if the associated purchase exists
    purchase = db.query(Purchase).filter(Purchase.id == purchase_detail.purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated purchase not found")

    # Check if the associated product exists
    product = db.query(Product).filter(Product.id == purchase_detail.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated product not found")

    # Check if the associated unit exists
    # unit = db.query(Unit).filter(Unit.id == purchase_detail.unit_id).first()
    # if not unit:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated unit not found")

    new_purchase_detail = PurchaseDetail(**purchase_detail.model_dump())
    db.add(new_purchase_detail)
    db.commit()
    db.refresh(new_purchase_detail)
    return new_purchase_detail


@router.put(
    "/{purchase_detail_id}",
    response_model=PurchaseDetailResponse,
    summary="Update a purchase detail",
    description="Update an existing purchase detail with the provided information.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PURCHASE_DETAILS
)
async def update(purchase_detail_id: int, purchase_detail: PurchaseDetailUpdate, db: db_dependency):
    existing_purchase_detail = db.query(PurchaseDetail).filter(PurchaseDetail.id == purchase_detail_id).first()
    if not existing_purchase_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase detail not found")

    # If purchase_id is being updated, check if the new purchase exists
    if purchase_detail.purchase_id is not None:
        purchase = db.query(Purchase).filter(Purchase.id == purchase_detail.purchase_id).first()
        if not purchase:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated purchase not found")

    # If product_id is being updated, check if the new product exists
    if purchase_detail.product_id is not None:
        product = db.query(Product).filter(Product.id == purchase_detail.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated product not found")

    # If unit_id is being updated, check if the new unit exists
    # if purchase_detail.unit_id is not None:
    #     unit = db.query(Unit).filter(Unit.id == purchase_detail.unit_id).first()
    #     if not unit:
    #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated unit not found")

    for key, value in purchase_detail.model_dump(exclude_unset=True).items():
        setattr(existing_purchase_detail, key, value)

    existing_purchase_detail.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(existing_purchase_detail)
    return existing_purchase_detail


@router.delete(
    "/{purchase_detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a purchase detail",
    description="Delete an existing purchase detail by its ID.",
    dependencies=CAN_DELETE_PURCHASE_DETAILS
)
async def delete(purchase_detail_id: int, db: db_dependency):
    existing_purchase_detail = db.query(PurchaseDetail).filter(PurchaseDetail.id == purchase_detail_id).first()
    if not existing_purchase_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase detail not found")

    db.delete(existing_purchase_detail)
    db.commit()
    return None