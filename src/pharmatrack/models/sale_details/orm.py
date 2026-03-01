from sqlalchemy import (
    BigInteger, TIMESTAMP, ForeignKey, Text, Numeric
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...db.session import Base
from datetime import datetime
from decimal import Decimal


class SaleDetail(Base):
    __tablename__ = "sale_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    sale_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id"), nullable=False, index=True
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="sale_details")
    product: Mapped["Product"] = relationship("Product", back_populates="sale_details")

    batch_usages: Mapped[list["SaleBatchUsage"]] = relationship(
        "SaleBatchUsage",
        back_populates="sale_detail",
        cascade="all, delete-orphan",
    )

    refund_products: Mapped[list["RefundProduct"]] = relationship(
        "RefundProduct",
        back_populates="sale_detail",
    )
