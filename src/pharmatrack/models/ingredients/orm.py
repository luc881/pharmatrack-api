from sqlalchemy import String, BigInteger, TIMESTAMP, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ...db.session import Base
from ..product_has_ingredients.orm import ProductHasIngredient


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    products: Mapped[list["ProductHasIngredient"]] = relationship(
        "ProductHasIngredient",
        back_populates="ingredient",
        cascade="all, delete-orphan"
    )