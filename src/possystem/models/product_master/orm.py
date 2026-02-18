from typing import List
from datetime import datetime

from sqlalchemy import String, BigInteger, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...db.session import Base


class ProductMaster(Base):
    __tablename__ = "product_master"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        nullable=False
    )

    # --- Relaciones ---
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="master",
        cascade="all, delete-orphan"
    )

