from sqlalchemy import BigInteger, SmallInteger, String, Double, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ...db.session import Base
from datetime import datetime

class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("suppliers.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    date_emision: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    total: Mapped[float] = mapped_column(Double, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    supplier = relationship("Supplier", back_populates="purchases")
    user = relationship("User", back_populates="purchases")
    details = relationship("PurchaseDetail", back_populates="purchase", cascade="all, delete-orphan")



# class Purchase(Base):
#     __tablename__ = "purchases"
#
#     id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
#     # warehouse_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("warehouses.id"))
#     user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
#     branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("branches.id"))
#     date_emision: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
#     state: Mapped[int] = mapped_column(SmallInteger, comment="1=SOLICITUD, 2=REVISION, 3=PARCIAL, 4=ENTREGADO")
#     type_comprobant: Mapped[str] = mapped_column(String(100))
#     n_comprobant: Mapped[str] = mapped_column(String(100))
#     supplier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("suppliers.id"))
#     total: Mapped[float] = mapped_column(Double)
#     importe: Mapped[float] = mapped_column(Double)
#     igv: Mapped[float] = mapped_column(Double)
#     date_entrega: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
#     created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now())
#     deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#
#     # Relationships
#     supplier = relationship("Supplier", back_populates="purchases")
#     branch = relationship("Branch", back_populates="purchases")
#     user = relationship("User", back_populates="purchases")
#     details = relationship("PurchaseDetail", back_populates="purchase")
#     # warehouse = relationship("Warehouse", back_populates="purchases")
