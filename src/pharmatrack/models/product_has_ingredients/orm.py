from sqlalchemy import String, BigInteger, ForeignKey, Double
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ...db.session import Base


class ProductHasIngredient(Base):
    __tablename__ = "product_has_ingredients"

    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True
    )

    ingredient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        primary_key=True
    )

    # ✅ Dosis numérica
    amount: Mapped[float] = mapped_column(Double, nullable=True)

    # ✅ Unidad (mg, g, ml, IU, etc.)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)

    # Relaciones
    ingredient: Mapped["Ingredient"] = relationship(
        "Ingredient",
        back_populates="products"
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="ingredients"
    )