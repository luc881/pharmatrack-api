"""Envíos sueltos: cotizar y generar una guía de Envia.com sin pedido del sitio.

No dependen de «Aceptar envíos»: ese interruptor solo decide si la tienda
ofrece envío a los clientes. Usan los permisos de pedidos.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from ...db.session import db_dependency
from ...models.customers.schemas import ShippingLabelRequest, ShippingRateRequest
from ...models.shipments.orm import Shipment
from ...utils import envia
from ...utils.logger import get_logger
from ...utils.pagination import paginate, PaginationParams, PaginatedResponse
from ...utils.permissions import CAN_READ_ORDERS, CAN_UPDATE_ORDERS
from ...utils.security import user_dependency

logger = get_logger(__name__)

router = APIRouter(prefix="/shipments", tags=["Shipments"])


class ShipmentCreate(ShippingLabelRequest):
    idempotency_key: str = Field(..., min_length=8, max_length=64)
    note: Optional[str] = Field(None, max_length=250)


class ShipmentResponse(BaseModel):
    id: int
    note: Optional[str] = None
    recipient_name: str
    recipient_phone: str
    address: str
    content: str
    carrier: Optional[str] = None
    service: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    label_url: Optional[str] = None
    cost: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=PaginatedResponse[ShipmentResponse],
            dependencies=CAN_READ_ORDERS, summary="Listar envíos sueltos")
def list_shipments(db: db_dependency, pagination: PaginationParams = Depends()):
    return paginate(db.query(Shipment).order_by(Shipment.id.desc()), pagination)


@router.post("/rates", dependencies=CAN_UPDATE_ORDERS,
             summary="Cotizar un envío suelto con todas las paqueterías")
def quote_shipment(body: ShippingRateRequest):
    return {"rates": envia.rates(body.destination.model_dump(), body.package.model_dump())}


@router.post("", response_model=ShipmentResponse, dependencies=CAN_UPDATE_ORDERS,
             summary="Generar la guía de un envío suelto (se cobra a la cuenta de Envia.com)")
def create_shipment(body: ShipmentCreate, db: db_dependency, token_data: user_dependency):
    d = body.destination
    address = ", ".join(filter(None, [
        " ".join(filter(None, [d.street, d.number])), d.district,
        f"{d.postal_code} {d.city}", d.state, d.reference,
    ]))
    shipment = Shipment(
        idempotency_key=body.idempotency_key, note=body.note,
        recipient_name=d.name, recipient_phone=d.phone, address=address,
        content=body.package.content, user_id=token_data["id"],
    )
    # El alta va ANTES de comprar: el índice único hace esperar a un segundo
    # clic simultáneo hasta que este termine, y entonces choca
    db.add(shipment)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return db.query(Shipment).filter(Shipment.idempotency_key == body.idempotency_key).one()

    try:
        label = envia.generate(d.model_dump(), body.package.model_dump(), body.carrier, body.service)
    except Exception:
        db.rollback()  # sin guía no queda registro, y la clave sirve para reintentar
        raise
    # La guía ya se cobró: si guardar fallara, que al menos quede en el log
    logger.info("Guía generada para envío suelto (%s): %s", body.note, label)

    shipment.carrier = label["carrier"]
    shipment.service = label["service"]
    shipment.tracking_number = label["tracking_number"]
    shipment.tracking_url = label["tracking_url"]
    shipment.label_url = label["label_url"]
    shipment.cost = Decimal(str(label["cost"])) if label["cost"] is not None else None
    db.commit()
    db.refresh(shipment)
    return shipment
