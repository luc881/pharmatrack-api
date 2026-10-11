"""Control de entregas en persona (ventas y cambios). Solo registro: no mueve
inventario ni modifica ventas o pedidos; sale_id/order_id son referencias."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import db_dependency
from ...models.animals.orm import Animal
from ...models.customers.orm import Order
from ...models.deliveries.orm import Delivery
from ...models.deliveries.schemas import (
    DeliveryCreate, DeliveryResponse, DeliveryStatusUpdate, DeliverySummary, DeliveryUpdate,
)
from ...models.sales.orm import Sale
from ...utils.permissions import CAN_CREATE_SALES, CAN_READ_SALES, CAN_UPDATE_SALES
from ...utils.security import user_dependency
from pharmatrack.utils.pagination import PaginatedResponse, PaginationParams, paginate

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


def _get(db: Session, delivery_id: int) -> Delivery:
    d = db.query(Delivery).options(joinedload(Delivery.user)).filter(Delivery.id == delivery_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    return d


def _validate(db: Session, data: DeliveryCreate):
    if data.sale_id and not db.get(Sale, data.sale_id):
        raise HTTPException(status_code=400, detail="Sale not found.")
    if data.order_id and not db.get(Order, data.order_id):
        raise HTTPException(status_code=400, detail="Order not found.")
    animal_ids = {i.animal_id for i in data.items_given if i.animal_id}
    if animal_ids and db.query(Animal).filter(Animal.id.in_(animal_ids)).count() != len(animal_ids):
        raise HTTPException(status_code=400, detail="Animal not found.")


def _apply(d: Delivery, data: DeliveryCreate):
    for k, v in data.model_dump(exclude={"status"}).items():
        setattr(d, k, v)
    _set_status(d, data.status)


def _set_status(d: Delivery, new_status: str):
    # delivered_at = cuándo se marcó entregada (se conserva si ya lo estaba)
    if new_status == "delivered":
        if d.status != "delivered" or d.delivered_at is None:  # None también en las nuevas
            d.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        d.delivered_at = None
    d.status = new_status


@router.get("/summary", response_model=DeliverySummary, dependencies=CAN_READ_SALES)
async def delivery_summary(db: db_dependency, date_from: Optional[date] = None, date_to: Optional[date] = None):
    """Cobrado por entregas en el rango (por fecha de la entrega, sin
    canceladas) y lo que falta por cobrar de todas las no canceladas."""
    active = db.query(Delivery).filter(Delivery.status != "cancelled")

    in_range = active.filter(Delivery.paid.is_(True))
    if date_from:
        in_range = in_range.filter(Delivery.scheduled_date >= date_from)
    if date_to:
        in_range = in_range.filter(Delivery.scheduled_date <= date_to)
    by_method = dict(
        in_range.with_entities(Delivery.payment_method, func.coalesce(func.sum(Delivery.amount), 0))
        .group_by(Delivery.payment_method).all()
    )
    unpaid = active.filter(Delivery.paid.is_(False), Delivery.amount > 0)
    return {
        "collected": sum(by_method.values(), Decimal(0)),
        "cash": by_method.get("cash", 0),
        "transfer": by_method.get("transfer", 0),
        "other": by_method.get("other", 0) + by_method.get(None, 0),
        "to_collect": unpaid.with_entities(func.coalesce(func.sum(Delivery.amount), 0)).scalar(),
        "to_collect_count": unpaid.count(),
        "pending_count": active.filter(Delivery.status == "pending").count(),
    }


@router.get("", response_model=PaginatedResponse[DeliveryResponse], dependencies=CAN_READ_SALES)
async def list_deliveries(
    db: db_dependency,
    status_: Optional[str] = Query(None, alias="status", pattern="^(pending|delivered|cancelled)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = Query(None, max_length=100),
    pagination: PaginationParams = Depends(),
):
    query = db.query(Delivery).options(joinedload(Delivery.user))
    if status_:
        query = query.filter(Delivery.status == status_)
    if date_from:
        query = query.filter(Delivery.scheduled_date >= date_from)
    if date_to:
        query = query.filter(Delivery.scheduled_date <= date_to)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            Delivery.buyer_name.ilike(like), Delivery.buyer_contact.ilike(like), Delivery.place.ilike(like),
        ))
    # Pendientes: la más próxima primero; el resto, lo más reciente primero
    if status_ == "pending":
        order = [Delivery.scheduled_date.asc(), Delivery.scheduled_time.asc().nulls_last(), Delivery.id.asc()]
    else:
        order = [Delivery.scheduled_date.desc(), Delivery.scheduled_time.desc().nulls_last(), Delivery.id.desc()]
    return paginate(query.order_by(*order), pagination)


@router.post("", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED, dependencies=CAN_CREATE_SALES)
async def create_delivery(data: DeliveryCreate, db: db_dependency, user: user_dependency):
    _validate(db, data)
    d = Delivery(user_id=user["id"])
    _apply(d, data)
    db.add(d)
    db.commit()
    return _get(db, d.id)


@router.put("/{delivery_id}", response_model=DeliveryResponse, dependencies=CAN_CREATE_SALES)
async def update_delivery(delivery_id: int, data: DeliveryUpdate, db: db_dependency):
    d = _get(db, delivery_id)
    _validate(db, data)
    _apply(d, data)
    db.commit()
    return _get(db, delivery_id)


@router.put("/{delivery_id}/status", response_model=DeliveryResponse, dependencies=CAN_CREATE_SALES)
async def update_delivery_status(delivery_id: int, data: DeliveryStatusUpdate, db: db_dependency):
    d = _get(db, delivery_id)
    _set_status(d, data.status)
    db.commit()
    return _get(db, delivery_id)


@router.delete("/{delivery_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=CAN_UPDATE_SALES)
async def delete_delivery(delivery_id: int, db: db_dependency):
    db.delete(_get(db, delivery_id))
    db.commit()
