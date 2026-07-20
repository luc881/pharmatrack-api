from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from ...db.session import get_db, db_dependency
from starlette import status
from pydantic import BaseModel, EmailStr

from ...models.sales.orm import Sale
from ...models.users.orm import User
from ...models.branches.orm import Branch
from ...models.sales.schemas import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    PaginatedResponse,
    PaginationParams,
)
from pharmatrack.types.sales import SaleStatusEnum
from ...utils.permissions import (
    CAN_READ_SALES, CAN_CREATE_SALES, CAN_UPDATE_SALES, CAN_DELETE_SALES
)
from pharmatrack.utils.pagination import paginate
from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
from pharmatrack.utils.sales_calculations import recalc_sale_totals
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE
from ...utils.logger import get_logger

logger = get_logger(__name__)



class EmailTicketRequest(BaseModel):
    email: EmailStr


router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


# =========================================================
# GET /
# =========================================================
_SALE_ORDERING_MAP = {
    "date_sale":  Sale.date_sale.asc(),
    "-date_sale": Sale.date_sale.desc(),
    "total":      Sale.total.asc(),
    "-total":     Sale.total.desc(),
}


@router.get(
    "",
    response_model=PaginatedResponse[SaleResponse],
    summary="List all sales",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
async def read_all(
    request: Request,
    db: db_dependency,
    pagination: PaginationParams = Depends(),
    status_filter: Optional[SaleStatusEnum] = None,
    user_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    ordering: Optional[str] = None,
):
    query = db.query(Sale)

    if status_filter is not None:
        query = query.filter(Sale.status == status_filter)
    if user_id is not None:
        query = query.filter(Sale.user_id == user_id)
    if branch_id is not None:
        query = query.filter(Sale.branch_id == branch_id)
    if date_from is not None:
        query = query.filter(Sale.date_sale >= date_from)
    if date_to is not None:
        query = query.filter(Sale.date_sale <= date_to)

    order_clause = _SALE_ORDERING_MAP.get(ordering) if ordering else None
    query = query.order_by(order_clause if order_clause is not None else Sale.date_sale.desc())

    return paginate(query, pagination)


# =========================================================
# GET /summary — corte de caja
# =========================================================
@router.get(
    "/summary",
    summary="Resumen de ventas completadas (corte de caja)",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
def sales_summary(
    db: db_dependency,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    from ...models.products.orm import Product
    from ...models.sale_details.orm import SaleDetail
    from ...models.sale_payments.orm import SalePayment

    sales_q = db.query(Sale).filter(Sale.status == SaleStatusEnum.COMPLETED)
    if date_from is not None:
        sales_q = sales_q.filter(Sale.date_sale >= date_from)
    if date_to is not None:
        sales_q = sales_q.filter(Sale.date_sale <= date_to)

    totals = sales_q.with_entities(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total), 0),
        func.coalesce(func.sum(Sale.subtotal), 0),
        func.coalesce(func.sum(Sale.tax), 0),
    ).first()

    sale_ids = sales_q.with_entities(Sale.id).subquery()

    discounts = (
        db.query(func.coalesce(func.sum(SaleDetail.discount), 0))
        .filter(SaleDetail.sale_id.in_(sale_ids))
        .scalar()
    )

    top_products = (
        db.query(
            Product.title,
            func.coalesce(func.sum(SaleDetail.quantity), 0),
            func.coalesce(func.sum(SaleDetail.total), 0),
        )
        .join(SaleDetail, SaleDetail.product_id == Product.id)
        .filter(SaleDetail.sale_id.in_(sale_ids))
        .group_by(Product.title)
        .order_by(func.sum(SaleDetail.total).desc())
        .limit(10)
        .all()
    )

    payments = (
        db.query(SalePayment.method_payment, func.coalesce(func.sum(SalePayment.amount), 0))
        .filter(SalePayment.sale_id.in_(sale_ids))
        .group_by(SalePayment.method_payment)
        .all()
    )

    return {
        "count": totals[0],
        "total": totals[1],
        "subtotal": totals[2],
        "tax": totals[3],
        "discounts": discounts,
        "top_products": [
            {"title": t, "quantity": float(q), "total": float(tot)} for t, q, tot in top_products
        ],
        "payments": [
            {"method": (m.value if hasattr(m, "value") else m), "amount": float(a)} for m, a in payments
        ],
    }


# =========================================================
# POST /{sale_id}/email-ticket
# =========================================================
@router.post(
    "/{sale_id}/email-ticket",
    summary="Enviar el ticket de la venta por correo",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
def email_ticket(sale_id: int, body: EmailTicketRequest, db: db_dependency):
    from ...models.products.orm import Product
    from ...models.sale_details.orm import SaleDetail
    from ...models.sale_payments.orm import SalePayment
    from ...utils.email import send_ticket_email
    from .settings import get_email_ticket_template
    from ...config import settings

    if not settings.resend_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Envio de correo no configurado (RESEND_API_KEY).")

    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    details = (
        db.query(SaleDetail, Product.title)
        .join(Product, Product.id == SaleDetail.product_id)
        .filter(SaleDetail.sale_id == sale_id)
        .all()
    )
    items = [
        {
            "title": title,
            "quantity": float(d.quantity),
            "unit_price": float(d.unit_price or 0),
            "discount": float(d.discount or 0),
            "subtotal": float(d.total if d.total is not None
                              else d.quantity * (d.unit_price or 0) - (d.discount or 0)),
        }
        for d, title in details
    ]
    pays = db.query(SalePayment).filter(SalePayment.sale_id == sale_id).all()
    payments = [
        {"method": (p.method_payment.value if hasattr(p.method_payment, "value") else p.method_payment),
         "amount": float(p.amount)}
        for p in pays
    ]
    total = float(sale.total or sum(i["subtotal"] for i in items))
    change = sum(p["amount"] for p in payments) - total
    date_str = (sale.date_sale or sale.created_at).strftime("%d/%m/%Y %H:%M")

    try:
        send_ticket_email(body.email, sale_id, date_str, items, payments, total, change,
                          template=get_email_ticket_template(db))
    except Exception:
        logger.exception("Fallo el envio del ticket sale_id=%s", sale_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="No se pudo enviar el correo.")
    return {"sent": True}


# =========================================================
# GET /{sale_id}
# =========================================================
@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get sale by ID",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
async def read_by_id(sale_id: int, db: db_dependency):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")
    return sale


# =========================================================
# POST /
# =========================================================
@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALES,
)
@limiter.limit(LIMIT_WRITE)
async def create(request: Request, sale: SaleCreate, db: db_dependency):
    if not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    new_sale = Sale(
        user_id=sale.user_id,
        branch_id=sale.branch_id,
        description=sale.description,
        status=SaleStatusEnum.DRAFT,
        subtotal=0,
        tax=0,
        discount=0,
        total=0,
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    logger.info("Sale created id=%s user_id=%s branch_id=%s", new_sale.id, sale.user_id, sale.branch_id)
    return new_sale


# =========================================================
# POST /{sale_id}/complete
# =========================================================
@router.post(
    "/{sale_id}/complete",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
def complete_sale(sale_id: int, db: db_dependency):
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.sale_details))
        .filter(Sale.id == sale_id)
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    if sale.status != SaleStatusEnum.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft sales can be completed")

    if not sale.sale_details:
        raise HTTPException(status_code=400, detail="Cannot complete an empty sale")

    from ...models.animals.orm import Animal
    from pharmatrack.types.animals import AnimalStatusEnum

    product_ids = [d.product_id for d in sale.sale_details]
    # Los paquetes se sustituyen por sus componentes: un animal dentro de un
    # paquete cuenta igual que uno vendido directo
    from ...utils.sales_stock import expand_bundle_product_ids
    effective_ids = expand_bundle_product_ids(db, product_ids)

    # Un animal reservado no puede venderse: hay que liberar la reserva primero
    reserved = db.query(Animal.code).filter(
        Animal.product_id.in_(effective_ids),
        Animal.status == AnimalStatusEnum.RESERVED.value,
    ).all()
    if reserved:
        codes = ", ".join(r.code for r in reserved)
        raise HTTPException(
            status_code=400,
            detail=f"Animal(es) reservado(s): {codes}. Libera la reserva antes de completar la venta.",
        )

    for detail in sale.sale_details:
        allocate_batches_for_sale_detail(db, detail)

    recalc_sale_totals(db, sale)
    sale.status = SaleStatusEnum.COMPLETED

    # Los animales pasan a "sold" solo cuando su stock llega a 0.
    # Individuales (lote de 1): igual que siempre. Cepas/paquetes con
    # unidades restantes siguen disponibles.
    from sqlalchemy import func
    from ...models.product_batch.orm import ProductBatch

    # La sesión corre con autoflush=False: sin esto la suma leería las
    # cantidades de ANTES del descuento de lotes
    db.flush()

    remaining = dict(
        db.query(ProductBatch.product_id, func.coalesce(func.sum(ProductBatch.quantity), 0))
        .filter(ProductBatch.product_id.in_(effective_ids))
        .group_by(ProductBatch.product_id)
        .all()
    )
    sold_out = [pid for pid in effective_ids if remaining.get(pid, 0) <= 0]
    if sold_out:
        db.query(Animal).filter(
            Animal.product_id.in_(sold_out)
        ).update({Animal.status: AnimalStatusEnum.SOLD.value}, synchronize_session=False)

    db.commit()
    db.refresh(sale)

    logger.info("Sale completed id=%s total=%s", sale.id, sale.total)
    return sale


# =========================================================
# PUT /{sale_id}
# =========================================================
@router.put(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Update a sale",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
async def update(sale_id: int, sale: SaleUpdate, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    if sale.user_id and not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if sale.branch_id and not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    if sale.status in (SaleStatusEnum.REFUNDED, SaleStatusEnum.PARTIALLY_REFUNDED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund statuses can only be set automatically by the refund system.")

    if existing_sale.status != SaleStatusEnum.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft sales can be modified.")

    for key, value in sale.model_dump(exclude_unset=True).items():
        setattr(existing_sale, key, value)

    db.commit()
    db.refresh(existing_sale)
    logger.info("Sale updated id=%s", sale_id)
    return existing_sale


# =========================================================
# DELETE /{sale_id}
# =========================================================
@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale",
    dependencies=CAN_DELETE_SALES,
)
async def delete(sale_id: int, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    from ...models.refund_products.orm import RefundProduct
    from ...models.sale_details.orm import SaleDetail

    sale_details = db.query(SaleDetail.id).filter(SaleDetail.sale_id == sale_id).all()
    sale_detail_ids = [sd.id for sd in sale_details]

    if sale_detail_ids:
        refund_count = db.query(func.count(RefundProduct.id)).filter(
            RefundProduct.sale_detail_id.in_(sale_detail_ids)
        ).scalar() or 0

        if refund_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a sale that has refunds. Cancel the refunds first.",
            )

    db.delete(existing_sale)
    db.commit()
    logger.info("Sale deleted id=%s", sale_id)
    return