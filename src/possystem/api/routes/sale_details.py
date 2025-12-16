from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db
from ...models.sale_details.schemas import (
    SaleDetailCreate,
    SaleDetailResponse,
    SaleDetailUpdate,
)
from ...models.sale_details.orm import SaleDetail
from ...models.sales.orm import Sale
from ...models.products.orm import Product
from ...utils.permissions import (
    CAN_READ_SALE_DETAILS,
    CAN_CREATE_SALE_DETAILS,
    CAN_UPDATE_SALE_DETAILS,
    CAN_DELETE_SALE_DETAILS,
)
from ...utils.sales_calculations import recalc_sale_totals
from decimal import Decimal

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/saledetails",
    tags=["Sale Details"]
)

# -----------------------
# GET ALL
# -----------------------
@router.get(
    "/",
    response_model=list[SaleDetailResponse],
    summary="List all sale details",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALE_DETAILS,
)
def read_all(db: db_dependency):
    return db.query(SaleDetail).all()


# -----------------------
# CREATE
# -----------------------


@router.post(
    "/",
    response_model=SaleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALE_DETAILS,
)
def create(sale_detail: SaleDetailCreate, db: db_dependency):

    sale = db.query(Sale).filter(Sale.id == sale_detail.sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Associated sale not found")

    if sale.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Cannot add details to a non-draft sale",
        )

    product = db.query(Product).filter(Product.id == sale_detail.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Associated product not found")

    # 🔥 Calculamos nosotros
    line_subtotal = (
        Decimal(sale_detail.price_unit) * Decimal(sale_detail.quantity)
    ) - Decimal(sale_detail.discount or 0)

    tax = Decimal(sale_detail.tax or 0)
    total = line_subtotal + tax

    new_detail = SaleDetail(
        sale_id=sale.id,
        product_id=product.id,
        quantity=sale_detail.quantity,
        price_unit=sale_detail.price_unit,
        discount=sale_detail.discount or 0,
        tax=tax,
        total=total,
        description=sale_detail.description,
    )

    db.add(new_detail)
    db.flush()  # 👈 importante

    # 🔁 Recalcula la venta
    recalc_sale_totals(db, sale)

    db.commit()
    db.refresh(new_detail)

    return new_detail



# -----------------------
# UPDATE
# -----------------------


@router.put(
    "/{sale_detail_id}",
    response_model=SaleDetailResponse,
    dependencies=CAN_UPDATE_SALE_DETAILS,
)
def update(
    sale_detail_id: int,
    sale_detail: SaleDetailUpdate,
    db: db_dependency,
):
    detail = db.query(SaleDetail).filter(SaleDetail.id == sale_detail_id).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Sale detail not found")

    sale = detail.sale
    if sale.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Cannot modify details of a non-draft sale",
        )

    data = sale_detail.model_dump(exclude_unset=True)

    # ✅ Validar cambio de producto
    if "product_id" in data:
        product = (
            db.query(Product)
            .filter(Product.id == data["product_id"])
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=404,
                detail="Associated product not found",
            )

    # 📝 Aplicar cambios
    for key, value in data.items():
        setattr(detail, key, value)

    # 🔥 Recalcular línea
    line_subtotal = (detail.price_unit * detail.quantity) - detail.discount
    detail.total = line_subtotal + detail.tax

    # 🔁 Recalcular venta
    recalc_sale_totals(db, sale)

    db.commit()
    db.refresh(detail)

    return detail




# -----------------------
# DELETE (HARD DELETE)
# -----------------------
@router.delete(
    "/{sale_detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale detail",
    dependencies=CAN_DELETE_SALE_DETAILS,
)
def delete(sale_detail_id: int, db: db_dependency):
    existing_sale_detail = (
        db.query(SaleDetail)
        .filter(SaleDetail.id == sale_detail_id)
        .first()
    )

    if not existing_sale_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale detail not found",
        )

    db.delete(existing_sale_detail)
    db.commit()
