from sqlalchemy import String, BigInteger, Boolean, TIMESTAMP, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...db.session import Base
from datetime import datetime


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=True)
    phone: Mapped[str] = mapped_column(String(25), nullable=True)
    address: Mapped[str] = mapped_column(String(250), nullable=True)
    rfc: Mapped[str] = mapped_column(String(50), nullable=True)  # o 'ruc', según el país
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    purchases = relationship("Purchase", back_populates="supplier")


# from sqlalchemy import String, BigInteger, SmallInteger, TIMESTAMP, Text
# from sqlalchemy.sql import func
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from ...db.session import Base
# from datetime import datetime
#
# class Supplier(Base):
#     __tablename__ = "suppliers"
#
#     id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
#     full_name: Mapped[str] = mapped_column(String(255), nullable=False)
#     imagen: Mapped[str] = mapped_column(String(255), nullable=True)
#     email: Mapped[str] = mapped_column(String(250), nullable=True, unique=True)
#     phone: Mapped[str] = mapped_column(String(25), nullable=True)
#     address: Mapped[str] = mapped_column(String(250), nullable=True)
#     state: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="1=active, 2=inactive")
#     created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now())
#     deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
#     ruc: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)  # Unique taxpayer ID
#
#     # Add relationships here if you have related tables
#     purchases = relationship("Purchase", back_populates="supplier")
