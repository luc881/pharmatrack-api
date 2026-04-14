from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from datetime import datetime, timezone
from ...models.sale_payments.schemas import SalePaymentCreate, SalePaymentResponse, SalePaymentUpdate
from ...models.sale_payments.orm import SalePayment
from ...utils.permissions import CAN_READ_SALE_PAYMENTS, CAN_CREATE_SALE_PAYMENTS, CAN_UPDATE_SALE_PAYMENTS, CAN_DELETE_SALE_PAYMENTS
from ...models.sales.orm import Sale


db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/salepayments",
    tags=["Sale Payments"]
)

@router.get(
    "",
    response_model=list[SalePaymentResponse],
    summary="List all sale payments",
    description="Retrieve all sale payments currently stored in the database.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALE_PAYMENTS
)
async def read_all(db: db_dependency):
    sale_payments = db.query(SalePayment).all()
    return sale_payments

@router.post(
    "",
    response_model=SalePaymentResponse,
    summary="Create a new sale payment",
    description="Create a new sale payment with the provided details.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALE_PAYMENTS
)
async def create(sale_payment: SalePaymentCreate, db: db_dependency):
    # Check if the associated sale exists
    sale = db.query(Sale).filter(Sale.id == sale_payment.sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated sale not found")

    new_sale_payment = SalePayment(**sale_payment.model_dump())
    db.add(new_sale_payment)
    db.commit()
    db.refresh(new_sale_payment)
    return new_sale_payment

@router.put(
    "/{sale_payment_id}",
    response_model=SalePaymentResponse,
    summary="Update a sale payment",
    description="Update the details of an existing sale payment by its ID.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALE_PAYMENTS
)
async def update(sale_payment_id: int, sale_payment: SalePaymentUpdate, db: db_dependency):
    existing_sale_payment = db.query(SalePayment).filter(SalePayment.id == sale_payment_id).first()
    if not existing_sale_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale payment not found")

    # check if the associated sale exists if sale_id is being updated
    if sale_payment.model_dump().get("sale_id") is not None:
        sale = db.query(Sale).filter(Sale.id == sale_payment.model_dump().get("sale_id")).first()
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated sale not found")

    for key, value in sale_payment.model_dump(exclude_unset=True).items():
        setattr(existing_sale_payment, key, value)

    db.commit()
    db.refresh(existing_sale_payment)
    return existing_sale_payment

@router.delete(
    "/{sale_payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale payment",
    description="Soft delete a sale payment by its ID.",
    dependencies=CAN_DELETE_SALE_PAYMENTS
)
async def delete(sale_payment_id: int, db: db_dependency):
    existing_sale_payment = db.query(SalePayment).filter(SalePayment.id == sale_payment_id).first()
    if not existing_sale_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale payment not found")

    existing_sale_payment.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return