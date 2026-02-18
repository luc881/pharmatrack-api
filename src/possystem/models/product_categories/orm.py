from sqlalchemy import String, BigInteger, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ...db.session import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    image: Mapped[str] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 🔥 Recursivo (padre)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("product_categories.id", ondelete="CASCADE"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relaciones
    parent = relationship(
        "ProductCategory",
        remote_side=[id],
        back_populates="children"
    )

    children = relationship(
        "ProductCategory",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    products = relationship("Product", back_populates="category")
