from sqlalchemy import (
    String, BigInteger, Double, Text, TIMESTAMP, Boolean, ForeignKey
)
from sqlalchemy.sql import func
from ...db.session import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..product_has_ingredients.orm import ProductHasIngredient
from typing import List



class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    image: Mapped[str] = mapped_column(String(250), nullable=True)

    brand_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("product_brands.id", ondelete="RESTRICT"),
        nullable=True
    )

    product_master_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("product_master.id", ondelete="SET NULL"),
        nullable=True
    )

    # --- Precios ---
    price_retail: Mapped[float] = mapped_column(Double, nullable=False)
    price_cost: Mapped[float] = mapped_column(Double, nullable=False)

    # --- Descripción y control ---
    description: Mapped[str] = mapped_column(Text, nullable=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    allow_without_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    # --- Descuentos / impuestos ---
    is_discount: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    max_discount: Mapped[float] = mapped_column(Double, nullable=True)
    is_taxable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    tax_percentage: Mapped[float] = mapped_column(Double, nullable=True)

    # --- Garantía ---
    allow_warranty: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    warranty_days: Mapped[float] = mapped_column(Double, nullable=True)

    # --- Unidades / fraccionamiento ---
    unit_name: Mapped[str] = mapped_column(String(50), nullable=False, default="pieza")
    base_unit_name: Mapped[str] = mapped_column(String(50), nullable=True)
    units_per_base: Mapped[float] = mapped_column(Double, nullable=True)

    # --- Unidad de venta ---
    is_unit_sale: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="0"
    )

    unit_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    base_unit_name: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    units_per_base: Mapped[float] = mapped_column(
        Double,
        nullable=True
    )

    # --- Tiempos ---
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now()
    )

    # --- Relaciones ---
    sale_details = relationship("SaleDetail", back_populates="product")
    refund_products = relationship("RefundProduct", back_populates="product")
    purchase_details = relationship("PurchaseDetail", back_populates="product")

    batches = relationship(
        "ProductBatch",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    master = relationship("ProductMaster", back_populates="products")
    brand = relationship("ProductBrand", back_populates="products")

    ingredients: Mapped[list["ProductHasIngredient"]] = relationship(
        "ProductHasIngredient",
        back_populates="product",
        cascade="all, delete-orphan"
    )
