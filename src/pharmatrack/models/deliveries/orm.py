from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, JSON, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...db.session import Base


class Delivery(Base):
    """Entrega en persona (p. ej. en el Metro) de una venta o un cambio.
    Solo es un registro: no mueve inventario ni toca ventas; sale_id/order_id
    son referencias opcionales a la venta del POS o al pedido web."""
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, server_default="sale")
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="pending", index=True)

    buyer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    buyer_contact: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    place: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # [{description, quantity, animal_id?}] — lo que se entrega / lo que se recibe
    items_given: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    items_received: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    paid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    sale_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User")

    @property
    def user_name(self) -> Optional[str]:
        return self.user.name if self.user else None
