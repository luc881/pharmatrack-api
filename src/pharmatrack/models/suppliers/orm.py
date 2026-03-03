from sqlalchemy import String, BigInteger, SmallInteger, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...db.session import Base
from datetime import datetime


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(250), nullable=True, unique=True)
    phone: Mapped[str] = mapped_column(String(25), nullable=True)
    address: Mapped[str] = mapped_column(String(250), nullable=True)
    rfc: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    purchases = relationship("Purchase", back_populates="supplier")