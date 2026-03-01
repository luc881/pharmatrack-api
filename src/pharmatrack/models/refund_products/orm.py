from sqlalchemy import BigInteger, Double, SmallInteger, TIMESTAMP, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...db.session import Base
from datetime import datetime

class RefundProduct(Base):
    __tablename__ = "refund_products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Double, nullable=False)
    sale_detail_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sale_details.id"), nullable=True)
    is_reintegrable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    reintegrated_batches: Mapped[dict] = mapped_column(JSON, default={})

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="refund_products")
    sale_detail: Mapped["SaleDetail"] = relationship("SaleDetail", back_populates="refund_products")
    user: Mapped["User"] = relationship("User", back_populates="refund_products")



