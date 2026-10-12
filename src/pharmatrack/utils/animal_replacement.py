"""Cambio de un ejemplar que murió por otro disponible.

Un ejemplar puede estar comprometido con un cliente de tres formas: reservado,
vendido en el POS (su lote fue el que se descontó) o en una entrega pendiente.
Si muere, `swap` pasa esos compromisos al reemplazo y `unswap` los regresa
(al borrar la baja en la bitácora).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.animals.orm import Animal
from ..models.deliveries.orm import Delivery
from ..models.product_batch.orm import ProductBatch
from ..models.sale_batch_usage.orm import SaleBatchUsage
from ..models.sale_details.orm import SaleDetail
from ..models.sales.orm import Sale
from ..types.animals import AnimalStatusEnum
from ..types.sales import SaleStatusEnum

SOLD_STATES = (SaleStatusEnum.COMPLETED, SaleStatusEnum.PARTIALLY_REFUNDED)
CDMX = timezone(timedelta(hours=-6))


def sale_usage(db: Session, animal: Animal) -> Optional[SaleBatchUsage]:
    """El renglón de la venta vigente que se llevó este ejemplar (el más reciente)."""
    return (
        db.query(SaleBatchUsage)
        .join(ProductBatch, ProductBatch.id == SaleBatchUsage.batch_id)
        .join(SaleDetail, SaleDetail.id == SaleBatchUsage.sale_detail_id)
        .join(Sale, Sale.id == SaleDetail.sale_id)
        .filter(ProductBatch.product_id == animal.product_id, Sale.status.in_(SOLD_STATES))
        .order_by(SaleBatchUsage.id.desc())
        .first()
    )


def pending_deliveries(db: Session, animal_id: int) -> list[Delivery]:
    # ponytail: items_given es JSON; se filtra en Python (pendientes son pocas)
    rows = db.query(Delivery).filter(Delivery.status == "pending").all()
    return [d for d in rows if any(i.get("animal_id") == animal_id for i in d.items_given or [])]


def commitments(db: Session, animal: Animal) -> dict:
    usage = sale_usage(db, animal) if animal.status == AnimalStatusEnum.SOLD.value else None
    sale = usage.sale_detail.sale if usage else None
    return {
        "status": animal.status,
        "sale": {"id": sale.id, "date_sale": sale.date_sale} if sale else None,
        "deliveries": [
            {"id": d.id, "buyer_name": d.buyer_name, "scheduled_date": d.scheduled_date}
            for d in pending_deliveries(db, animal.id)
        ],
    }


def _note(text: Optional[str], line: str) -> str:
    return f"{text}\n{line}" if text else line


def _move_deliveries(db: Session, src: Animal, dst: Animal) -> None:
    for d in pending_deliveries(db, src.id):
        items = []
        for i in d.items_given:
            if i.get("animal_id") == src.id:
                desc = i.get("description") or ""
                i = {**i, "animal_id": dst.id,
                     "description": desc.replace(src.code, dst.code) if src.code in desc else dst.code}
            items.append(i)
        d.items_given = items  # lista nueva: SQLAlchemy no ve cambios dentro del JSON
        d.notes = _note(d.notes, f"Cambio: {src.code} → {dst.code}")


def _first_batch(db: Session, animal: Animal, with_stock: bool) -> Optional[ProductBatch]:
    q = db.query(ProductBatch).filter(ProductBatch.product_id == animal.product_id)
    if with_stock:
        q = q.filter(ProductBatch.quantity > 0)
    return q.order_by(ProductBatch.id).with_for_update().first()


def validate_replacement(db: Session, dead: Animal, replacement_id: int) -> Animal:
    repl = db.get(Animal, replacement_id)
    if not repl or repl.id == dead.id or repl.species_id != dead.species_id:
        raise HTTPException(status_code=400, detail="El reemplazo debe ser otro ejemplar de la misma especie.")
    if repl.status != AnimalStatusEnum.AVAILABLE.value or not _first_batch(db, repl, with_stock=True):
        raise HTTPException(status_code=400, detail=f"{repl.code} no está disponible para el cambio.")
    return repl


def swap(db: Session, dead: Animal, repl: Animal, prev_status: str) -> Optional[int]:
    """Pasa reserva, venta y entregas pendientes de `dead` a `repl`.
    Devuelve el id del uso de lote movido (para deshacer), si era venta."""
    usage_id = None
    if prev_status == AnimalStatusEnum.RESERVED.value:
        repl.status = AnimalStatusEnum.RESERVED.value
    elif prev_status == AnimalStatusEnum.SOLD.value:
        usage = sale_usage(db, dead)
        if usage:
            batch = _first_batch(db, repl, with_stock=True)
            batch.quantity -= usage.quantity_used
            usage.batch_id = batch.id
            detail = usage.sale_detail
            if detail.product_id == dead.product_id:  # si iba en un paquete, el renglón es del paquete
                detail.product_id = repl.product_id
            today = datetime.now(CDMX).date().isoformat()
            detail.sale.description = _note(
                detail.sale.description, f"Cambio por baja ({today}): {dead.code} → {repl.code}"
            )
            repl.status = AnimalStatusEnum.SOLD.value
            usage_id = usage.id
    _move_deliveries(db, dead, repl)
    return usage_id


def unswap(db: Session, dead: Animal, repl: Optional[Animal], prev_status: str, usage_id: Optional[int]) -> None:
    """Regresa a `dead` lo que `swap` le pasó a `repl`. Si el reemplazo ya se
    usó para otra cosa (otra venta, otra reserva), no adivina: avisa."""
    if repl is None:
        raise HTTPException(status_code=400, detail="El ejemplar de reemplazo ya no existe; no se puede deshacer el cambio.")
    if usage_id:
        usage = db.get(SaleBatchUsage, usage_id)
        if not usage or usage.batch.product_id != repl.product_id or usage.sale_detail.sale.status not in SOLD_STATES:
            raise HTTPException(
                status_code=409,
                detail=f"La venta de {repl.code} cambió (devolución u otra edición); deshaz el cambio a mano.",
            )
        dead_batch = _first_batch(db, dead, with_stock=False)
        usage.batch.quantity += usage.quantity_used
        usage.batch_id = dead_batch.id
        detail = usage.sale_detail
        if detail.product_id == repl.product_id:
            detail.product_id = dead.product_id
        detail.sale.description = _note(detail.sale.description, f"Se deshizo el cambio {dead.code} → {repl.code}")
        repl.status = AnimalStatusEnum.AVAILABLE.value
    elif prev_status == AnimalStatusEnum.RESERVED.value:
        if repl.status == AnimalStatusEnum.RESERVED.value:
            repl.status = AnimalStatusEnum.AVAILABLE.value
    _move_deliveries(db, repl, dead)
