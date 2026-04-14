from sqlalchemy import (
    String, BigInteger, TIMESTAMP, ForeignKey, Numeric, Enum as SAEnum
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...db.session import Base
from datetime import datetime
from decimal import Decimal
from pharmatrack.types.sales import PaymentMethodEnum


class SalePayment(Base):
    __tablename__ = "sale_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    sale_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales.id"), nullable=False, index=True
    )

    method_payment: Mapped[PaymentMethodEnum] = mapped_column(
        SAEnum(PaymentMethodEnum, name="paymentmethodenum", create_type=False),
        nullable=False,
    )

    transaction_number: Mapped[str] = mapped_column(String(100), nullable=True)
    bank: Mapped[str] = mapped_column(String(100), nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    # Relationship
    sale: Mapped["Sale"] = relationship("Sale", back_populates="sale_payments")
