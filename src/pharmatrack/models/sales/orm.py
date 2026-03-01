from sqlalchemy import (
    String, BigInteger, TIMESTAMP, ForeignKey, Text, Numeric
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...db.session import Base
from datetime import datetime
from decimal import Decimal


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id"), nullable=False, index=True
    )

    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed"
    )  # completed | cancelled | refunded

    description: Mapped[str] = mapped_column(Text, nullable=True)

    date_sale: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sales")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="sales")

    sale_details: Mapped[list["SaleDetail"]] = relationship(
        "SaleDetail",
        back_populates="sale",
        cascade="all, delete-orphan",
    )

    sale_payments: Mapped[list["SalePayment"]] = relationship(
        "SalePayment",
        back_populates="sale",
        cascade="all, delete-orphan",
    )
