from sqlalchemy import String, BigInteger, Double, Date, ForeignKey, Integer, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from ...db.session import Base
from typing import Optional


class ProductBatch(Base):
    __tablename__ = "product_batches"
    __table_args__ = (
        UniqueConstraint("product_id", "lot_code", name="uq_product_lot_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lot_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True  # <-- CORRECTO: quitamos unique=True
    )

    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="batches")
    sale_usages: Mapped[list["SaleBatchUsage"]] = relationship("SaleBatchUsage", back_populates="batch")
