"""Clientes del sitio público y sus pedidos.

Tabla APARTE de `users` a propósito: un cliente que entra con Google jamás
debe poder heredar un role_id ni permisos del dashboard. Los dos mundos no
comparten tabla, ni token (ver create_customer_token en utils/security.py).

Favoritos y carrito viven como JSON en la propia fila: es exactamente la
forma que el navegador ya guardaba en localStorage, y nunca hace falta
consultarlos al revés ("quién marcó X").
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Text, String, Integer, Numeric, BigInteger, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.sql import func

from ...db.session import Base

# Un pedido NO es una venta: es una solicitud. Cuando la confirmas registras
# la venta en el POS como siempre, para no ensuciar stock ni corte de caja.
# "paid" solo lo pone el webhook de Mercado Pago, nunca el dashboard a mano.
ORDER_STATUSES = ("pending", "paid", "confirmed", "completed", "cancelled")

# Entrega personal en CDMX = el precio del catálogo ES el total, así que se
# puede cobrar en línea de una vez. Con envío hay que cotizar antes: ese
# sigue por link de pago manual desde WhatsApp.
DELIVERY_METHODS = ("pickup", "shipping")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    google_sub: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Texto ya formateado a partir de los campos de abajo. Se conserva porque
    # es lo que copian los pedidos y los correos: los campos estructurados se
    # agregaron debajo sin romper nada de lo que ya consumía `address`.
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    street: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ext_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    int_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    neighborhood: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    address_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    favorites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    cart: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="customer", order_by="Order.id.desc()"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Folio visible (PD-XXXXXXXX, como el code de los animales): no secuencial
    # para no revelar el volumen de pedidos
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")

    # Datos de contacto congelados al momento del pedido: si el cliente
    # cambia su teléfono después, este pedido conserva con qué se hizo.
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False,
                                                 server_default="shipping")
    # id del pago en Mercado Pago; sirve de idempotencia (el webhook llega
    # varias veces por el mismo pago) y para buscarlo en su panel
    payment_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders", lazy="selectin")
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", lazy="selectin", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=False)
    # Llave del catálogo: "pr-{producto}", "m{morph}-{escala|u}", "s{especie}-{escala|u}"
    item_key: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Precio congelado: el catálogo puede subir mañana, este pedido no.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")

    @property
    def subtotal(self) -> Decimal:
        return Decimal(self.quantity) * self.unit_price
