from sqlalchemy import BigInteger, Numeric, Date, TIMESTAMP, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ...db.session import Base
from datetime import datetime, date
from decimal import Decimal
from typing import Optional


class PurchaseDetail(Base):
    __tablename__ = "purchase_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    purchase_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("purchases.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    lot_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    purchase = relationship("Purchase", back_populates="details")
    product = relationship("Product", back_populates="purchase_details")