from sqlalchemy import BigInteger, SmallInteger, Double, TIMESTAMP, Text, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ...db.session import Base
from datetime import datetime

class PurchaseDetail(Base):
    __tablename__ = "purchase_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purchase_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchases.id"))
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Double, nullable=False)
    unit_price: Mapped[float] = mapped_column(Double, nullable=False)
    expiration_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    lot_code: Mapped[str] = mapped_column(String(100), nullable=True)

    purchase = relationship("Purchase", back_populates="details")
    product = relationship("Product", back_populates="purchase_details")


# class PurchaseDetail(Base):
#     __tablename__ = "purchase_details"
#
#     id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
#     purchase_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchases.id"))
#     product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"))
#     # unit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("units.id"))
#     quantity: Mapped[float] = mapped_column(Double)
#     unit_price: Mapped[float] = mapped_column(Double)
#     total_price: Mapped[float] = mapped_column(Double)
#     status: Mapped[int] = mapped_column(SmallInteger, comment="1=REQUESTED, 2=DELIVERED")
#     delivered_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
#     delivered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now())
#     deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
#
#     # Relationships
#     purchase = relationship("Purchase", back_populates="details")
#     product = relationship("Product", back_populates="purchase_details")
#     # unit = relationship("Unit", back_populates="purchase_details")
#     # delivered_by = relationship(
#     #     "User",
#     #     back_populates="delivered_purchase_details",
#     #     foreign_keys=[delivered_by_id]
#     # )
