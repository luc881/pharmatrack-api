from sqlalchemy import (
    BigInteger,
    Integer,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ...db.session import Base


class SaleBatchUsage(Base):
    __tablename__ = "sale_batch_usages"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    sale_detail_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sale_details.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    batch_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("product_batches.id"),
        nullable=False,
        index=True,
    )

    quantity_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # -----------------------
    # Relationships
    # -----------------------
    sale_detail: Mapped["SaleDetail"] = relationship(
        "SaleDetail",
        back_populates="batch_usages",
    )

    batch: Mapped["ProductBatch"] = relationship(
        "ProductBatch",
        back_populates="sale_usages",
    )
