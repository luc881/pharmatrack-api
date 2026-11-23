from fastapi import Depends, HTTPException, APIRouter, Request, Response
from typing import Annotated, Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime
from ...db.session import get_db, db_dependency
from starlette import status
from pydantic import BaseModel, EmailStr

from ...models.sales.orm import Sale
from ...models.users.orm import User
from ...models.branches.orm import Branch
from ...models.sale_payments.orm import SalePayment
from ...models.sales.schemas import (
    SaleCreate,
    SaleCheckout,
    SaleUpdate,
    SaleResponse,
    OwnerCut,
    OwnerCutProduct,
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
from ...utils.security import user_dependency
from .sale_details import build_sale_detail
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
def read_all(
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

    # Todas las líneas por producto (sin tope): la hoja de inventario del
    # dashboard cruza esto con el producto gemelo de cada animal.
    by_product = (
        db.query(
            SaleDetail.product_id,
            func.coalesce(func.sum(SaleDetail.quantity), 0),
            func.coalesce(func.sum(SaleDetail.total), 0),
        )
        .filter(SaleDetail.sale_id.in_(sale_ids))
        .group_by(SaleDetail.product_id)
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
        "by_product": [
            {"product_id": pid, "quantity": float(q), "total": float(tot)} for pid, q, tot in by_product
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
    from pharmatrack.utils.mx_day import MX_OFFSET
    date_str = (sale.date_sale - MX_OFFSET).strftime("%d/%m/%Y %H:%M")

    try:
        send_ticket_email(body.email, sale_id, date_str, items, payments, total, change,
                          template=get_email_ticket_template(db))
    except Exception:
        logger.exception("Fallo el envio del ticket sale_id=%s", sale_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="No se pudo enviar el correo.")
    return {"sent": True}


# =========================================================
# GET /report/by-owner — cuánto vendió cada dueño
# =========================================================
# Va antes de /{sale_id}: si no, "report" se leería como un id.
@router.get(
    "/report/by-owner",
    response_model=list[OwnerCut],
    summary="Corte por dueño: productos propios y de cada proveedor en consigna",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
def report_by_owner(request: Request, db: db_dependency, date_from: date, date_to: date,
                    branch_id: Optional[int] = None):
    """Se reparte por línea (su total ya trae descuento e impuesto), así que
    un ticket mezclado se separa solo. No reparte por forma de pago."""
    from datetime import time, timedelta
    from ...models.products.orm import Product
    from ...models.sale_details.orm import SaleDetail
    from ...models.suppliers.orm import Supplier

    # Los días son los de México (UTC-6, sin horario de verano); date_sale va en UTC
    start = datetime.combine(date_from, time.min) + timedelta(hours=6)
    end = datetime.combine(date_to, time.min) + timedelta(days=1, hours=6)

    query = (
        db.query(Product.consignor_id, Supplier.name, Product.id, Product.title,
                 func.sum(SaleDetail.quantity), func.sum(SaleDetail.total))
        .join(SaleDetail, SaleDetail.product_id == Product.id)
        .join(Sale, Sale.id == SaleDetail.sale_id)
        .outerjoin(Supplier, Supplier.id == Product.consignor_id)
        .filter(Sale.status == SaleStatusEnum.COMPLETED,
                Sale.date_sale >= start, Sale.date_sale < end)
        .group_by(Product.consignor_id, Supplier.name, Product.id, Product.title)
        .order_by(Product.title, Product.id)
    )
    if branch_id is not None:
        query = query.filter(Sale.branch_id == branch_id)

    owners: dict = {}
    for consignor_id, name, product_id, title, units, amount in query.all():
        cut = owners.setdefault(consignor_id, OwnerCut(
            consignor_id=consignor_id, owner=name or "Propio", units=0, amount=0, products=[]))
        cut.units += float(units)
        cut.amount += amount
        cut.products.append(OwnerCutProduct(product_id=product_id, title=title,
                                            units=float(units), amount=amount))
    # Propio primero; después por nombre
    return sorted(owners.values(), key=lambda c: (c.consignor_id is not None, c.owner.lower()))


# =========================================================
# GET /export — Excel del periodo
# =========================================================
# Va antes de /{sale_id}: si no, "export" se leería como un id.
@router.get(
    "/export",
    summary="Excel con todas las ventas del periodo y lo que se vendió en cada una",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
def export_sales(
    request: Request,
    db: db_dependency,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status_filter: Optional[SaleStatusEnum] = None,
):
    from datetime import time, timedelta
    from ...models.sale_details.orm import SaleDetail
    from ...models.suppliers.orm import Supplier
    from pharmatrack.utils.mx_day import MX_OFFSET
    from pharmatrack.utils.sales_export import sales_workbook

    query = db.query(Sale).options(
        selectinload(Sale.sale_details).joinedload(SaleDetail.product),
        selectinload(Sale.sale_payments),
        joinedload(Sale.user),
        joinedload(Sale.branch),
    )
    if date_from is not None:
        query = query.filter(Sale.date_sale >= datetime.combine(date_from, time.min) + MX_OFFSET)
    if date_to is not None:
        query = query.filter(
            Sale.date_sale < datetime.combine(date_to, time.min) + timedelta(days=1) + MX_OFFSET)
    if status_filter is not None:
        query = query.filter(Sale.status == status_filter)

    period = " ".join(filter(None, [
        date_from and f"del {date_from:%d/%m/%Y}",
        date_to and f"al {date_to:%d/%m/%Y}",
    ])) or "Todas"
    owners = dict(db.query(Supplier.id, Supplier.name).tuples().all())
    return Response(
        sales_workbook(query.order_by(Sale.date_sale, Sale.id).all(), owners, period),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="ventas.xlsx"'},
    )


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
def read_by_id(sale_id: int, db: db_dependency):
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
def create(request: Request, sale: SaleCreate, db: db_dependency):
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
        # Candado: dos «completar» a la vez (doble clic, reintento) se forman y
        # el segundo ya ve la venta completada; sin esto descontaban stock dos veces.
        .with_for_update(of=Sale)
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    if sale.status != SaleStatusEnum.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft sales can be completed")

    _complete(db, sale)
    db.commit()
    db.refresh(sale)

    logger.info("Sale completed id=%s total=%s", sale.id, sale.total)
    return sale


# =========================================================
# POST /{sale_id}/cancel — se arrepintieron después de cobrar
# =========================================================
@router.post(
    "/{sale_id}/cancel",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    dependencies=CAN_DELETE_SALES,
)
def cancel_sale(sale_id: int, db: db_dependency):
    """Regresa a sus lotes lo que se descontó, reactiva los animales que
    vuelven a tener stock y deja la venta CANCELLED: queda en el historial,
    fuera del corte y los reportes (solo cuentan COMPLETED)."""
    from ...models.animals.orm import Animal
    from ...models.product_batch.orm import ProductBatch
    from ...models.refund_products.orm import RefundProduct
    from ...models.sale_batch_usage.orm import SaleBatchUsage
    from ...models.sale_details.orm import SaleDetail
    from ...utils.sales_stock import expand_bundle_product_ids
    from pharmatrack.types.animals import AnimalStatusEnum

    sale = db.query(Sale).filter(Sale.id == sale_id).with_for_update().first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.status != SaleStatusEnum.COMPLETED:
        raise HTTPException(status_code=400, detail="Solo se puede cancelar una venta completada.")

    detail_ids = [d.id for d in db.query(SaleDetail.id).filter(SaleDetail.sale_id == sale_id)]
    if db.query(RefundProduct.id).filter(RefundProduct.sale_detail_id.in_(detail_ids)).first():
        raise HTTPException(status_code=400,
                            detail="La venta tiene devoluciones; no se puede cancelar.")

    usages = db.query(SaleBatchUsage).filter(SaleBatchUsage.sale_detail_id.in_(detail_ids)).all()
    for usage in usages:
        batch = db.query(ProductBatch).filter(ProductBatch.id == usage.batch_id).with_for_update().first()
        if batch:
            batch.quantity += usage.quantity_used
    db.flush()

    # Vendido (stock 0) que vuelve a tener piezas: otra vez disponible
    product_ids = [d.product_id for d in db.query(SaleDetail.product_id).filter(
        SaleDetail.sale_id == sale_id)]
    effective_ids = expand_bundle_product_ids(db, product_ids)
    with_stock = [pid for (pid,) in db.query(ProductBatch.product_id)
                  .filter(ProductBatch.product_id.in_(effective_ids))
                  .group_by(ProductBatch.product_id)
                  .having(func.sum(ProductBatch.quantity) > 0)]
    if with_stock:
        db.query(Animal).filter(
            Animal.product_id.in_(with_stock),
            Animal.status == AnimalStatusEnum.SOLD.value,
        ).update({Animal.status: AnimalStatusEnum.AVAILABLE.value}, synchronize_session=False)

    sale.status = SaleStatusEnum.CANCELLED
    db.commit()
    db.refresh(sale)
    logger.info("Sale cancelled id=%s", sale.id)
    return sale


def _complete(db, sale: Sale) -> None:
    """Valida, descuenta stock y deja la venta COMPLETED, sin commit. La usan
    POST /{id}/complete y POST /checkout."""
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

    # Uno que murió (baja en la bitácora) puede seguir en un borrador o paquete
    deceased = db.query(Animal.code).filter(
        Animal.product_id.in_(effective_ids),
        Animal.status == AnimalStatusEnum.DECEASED.value,
    ).all()
    if deceased:
        codes = ", ".join(r.code for r in deceased)
        raise HTTPException(
            status_code=400,
            detail=f"Animal(es) que murieron: {codes}. Quítalos de la venta.",
        )

    # Pie de cría o crianza: no se cobran hasta ponerlos en venta
    not_for_sale = db.query(Animal.code).filter(
        Animal.product_id.in_(effective_ids),
        Animal.purpose != "sale",
    ).all()
    if not_for_sale:
        codes = ", ".join(r.code for r in not_for_sale)
        raise HTTPException(
            status_code=400,
            detail=f"Animal(es) que no están en venta: {codes}. Ponlos en venta o quítalos de la venta.",
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
            Animal.product_id.in_(sold_out),
            Animal.status != AnimalStatusEnum.DECEASED.value,
        ).update({Animal.status: AnimalStatusEnum.SOLD.value}, synchronize_session=False)


# =========================================================
# POST /checkout — la venta completa en una transacción
# =========================================================
@router.post(
    "/checkout",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar y completar una venta en una sola petición",
    dependencies=CAN_CREATE_SALES + CAN_UPDATE_SALES,
)
@limiter.limit(LIMIT_WRITE)
def checkout(request: Request, body: SaleCheckout, db: db_dependency, token_data: user_dependency):
    """Venta, líneas, pagos y descuento de stock: todo o nada. Si algo falla
    no queda ni un borrador. Con `idempotency_key`, repetir la petición (doble
    clic, respuesta perdida) devuelve la venta ya hecha en vez de cobrar otra."""
    key = body.idempotency_key

    def already_done():
        return db.query(Sale).filter(Sale.idempotency_key == key).first() if key else None

    existing = already_done()
    if existing:
        return existing

    if not db.query(Branch).filter_by(id=body.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    # Cobrar a otro precio que el del producto: solo un administrador
    if any(i.unit_price is not None for i in body.items) and token_data.get("user_role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo un administrador puede cambiar el precio al cobrar.")

    sale = Sale(
        user_id=token_data["id"],
        branch_id=body.branch_id,
        description=body.description,
        status=SaleStatusEnum.DRAFT,
        subtotal=0, tax=0, discount=0, total=0,
        idempotency_key=key,
    )
    if body.sold_at:
        sale.date_sale = body.sold_at
    db.add(sale)
    try:
        db.flush()
    except IntegrityError:
        # Otra petición con la misma llave ganó la carrera: el índice único la
        # hizo esperar a que la primera terminara. Se devuelve esa venta.
        db.rollback()
        existing = already_done()
        if existing:
            return existing
        raise

    for line in body.items:
        build_sale_detail(db, sale, line)
    for payment in body.payments:
        db.add(SalePayment(sale_id=sale.id, **payment.model_dump()))
    db.flush()
    db.expire(sale, ["sale_details"])

    _complete(db, sale)
    db.commit()
    db.refresh(sale)

    logger.info("Sale checkout id=%s total=%s", sale.id, sale.total)
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
def update(sale_id: int, sale: SaleUpdate, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    if sale.user_id and not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if sale.branch_id and not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    if sale.status in (SaleStatusEnum.REFUNDED, SaleStatusEnum.PARTIALLY_REFUNDED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund statuses can only be set automatically by the refund system.")

    # Completar solo por POST /{id}/complete: ahí se descuenta stock y se
    # recalculan totales. Por aquí quedaría "completada" sin tocar inventario.
    if sale.status == SaleStatusEnum.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use POST /sales/{id}/complete to complete a sale.")

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
def delete(sale_id: int, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    # Borrarla no regresa su stock a los lotes: primero se cancela
    if existing_sale.status == SaleStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una venta cobrada no se borra: Cancela la venta (regresa lo vendido al inventario).",
        )

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