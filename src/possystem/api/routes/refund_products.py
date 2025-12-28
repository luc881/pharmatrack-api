from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session, joinedload
from starlette import status
from datetime import datetime

from ...db.session import get_db
from ...models.refund_products.orm import RefundProduct
from ...models.refund_products.schemas import RefundProductCreate, RefundProductResponse, RefundProductUpdate
from ...models.products.orm import Product
from ...models.sale_details.orm import SaleDetail
from ...models.users.orm import User
from ...models.product_batch.orm import ProductBatch
from ...utils.permissions import CAN_READ_REFUND_PRODUCTS, CAN_CREATE_REFUND_PRODUCTS, CAN_UPDATE_REFUND_PRODUCTS, CAN_DELETE_REFUND_PRODUCTS

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/refundproducts",
    tags=["Refund Products"]
)


# -----------------------
# GET ALL
# -----------------------
@router.get(
    "/",
    response_model=list[RefundProductResponse],
    summary="List all refund products",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_REFUND_PRODUCTS
)
async def read_all(db: db_dependency):
    return db.query(RefundProduct).all()


# -----------------------
# CREATE
# -----------------------
@router.post(
    "/",
    response_model=RefundProductResponse,
    summary="Create a new refund product",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_REFUND_PRODUCTS
)
async def create(refund_product: RefundProductCreate, db: db_dependency):
    # Validar producto
    product = db.query(Product).filter(Product.id == refund_product.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Associated product not found")

    # Validar sale detail si se proporciona
    sale_detail = None
    if refund_product.sale_detail_id:
        sale_detail = db.query(SaleDetail).options(joinedload(SaleDetail.batch_usages)).filter(
            SaleDetail.id == refund_product.sale_detail_id
        ).first()
        if not sale_detail:
            raise HTTPException(status_code=404, detail="Associated sale detail not found")

    # Validar usuario si se proporciona
    if refund_product.user_id:
        user = db.query(User).filter(User.id == refund_product.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Associated user not found")

    new_refund = RefundProduct(**refund_product.model_dump())
    db.add(new_refund)

    # -----------------------
    # Reintegrar stock a lotes originales
    # -----------------------
    if refund_product.is_reintegrable and sale_detail:
        for usage in sale_detail.batch_usages:
            batch = db.query(ProductBatch).filter(ProductBatch.id == usage.batch_id).with_for_update().first()
            if not batch:
                continue  # o podrías lanzar error
            batch.quantity += usage.quantity_used

    db.commit()
    db.refresh(new_refund)
    return new_refund


# -----------------------
# UPDATE
# -----------------------
@router.put(
    "/{id}",
    response_model=RefundProductResponse,
    summary="Update an existing refund product",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_REFUND_PRODUCTS
)
async def update(id: int, refund_product: RefundProductUpdate, db: db_dependency):
    existing_refund = db.query(RefundProduct).filter(RefundProduct.id == id).first()
    if not existing_refund:
        raise HTTPException(status_code=404, detail="Refund product not found")

    # Validaciones
    if refund_product.product_id:
        product = db.query(Product).filter(Product.id == refund_product.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Associated product not found")

    if refund_product.sale_detail_id:
        sale_detail = db.query(SaleDetail).filter(SaleDetail.id == refund_product.sale_detail_id).first()
        if not sale_detail:
            raise HTTPException(status_code=404, detail="Associated sale detail not found")

    if refund_product.user_id:
        user = db.query(User).filter(User.id == refund_product.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Associated user not found")

    # Aplicar cambios
    for key, value in refund_product.model_dump(exclude_unset=True).items():
        setattr(existing_refund, key, value)

    db.commit()
    db.refresh(existing_refund)
    return existing_refund


# -----------------------
# DELETE
# -----------------------
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a refund product",
    dependencies=CAN_DELETE_REFUND_PRODUCTS
)
async def delete(id: int, db: db_dependency):
    existing_refund = db.query(RefundProduct).filter(RefundProduct.id == id).first()
    if not existing_refund:
        raise HTTPException(status_code=404, detail="Refund product not found")

    db.delete(existing_refund)
    db.commit()
    return
