"""Envíos sueltos: guías de Envia.com que no salen de un pedido del sitio
(una venta por WhatsApp, un regalo, una reposición)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...db.session import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # La pone el dashboard al abrir el formulario: dos clics en «Generar guía»
    # chocan aquí y no compran dos guías
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(String(100), nullable=False)
    # Se llenan cuando Envia devuelve la guía (misma transacción que el alta)
    carrier: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    service: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    tracking_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    label_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
