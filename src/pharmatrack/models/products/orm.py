from sqlalchemy import (
    String, BigInteger, Double, Numeric, Text, TIMESTAMP, Boolean, ForeignKey,
    Integer, UniqueConstraint
)
from sqlalchemy.sql import func
from ...db.session import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from ..product_has_ingredients.orm import ProductHasIngredient


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), nullable=False, unique=True, index=True)
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

    product_category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("product_categories.id", ondelete="RESTRICT"),
        nullable=False
    )

    # --- Precios ---
    price_retail: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # --- Descripción y control ---
    description: Mapped[str] = mapped_column(Text, nullable=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    # Precio anterior (tachado) para ofertas en la tienda; lo que se cobra
    # sigue siendo price_retail
    compare_at_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)

    # --- Descuentos / impuestos ---
    max_discount: Mapped[float] = mapped_column(Double, nullable=True)
    tax_percentage: Mapped[float] = mapped_column(Double, nullable=True)

    # --- Garantía ---
    allow_warranty: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    warranty_days: Mapped[float] = mapped_column(Double, nullable=True)

    # --- Trazabilidad de lotes ---
    tracks_batches: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    # Visible en el catálogo del sitio público (insumos de terrario, etc.)
    show_online: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    # --- Unidades / fraccionamiento ---
    is_unit_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    unit_name: Mapped[str] = mapped_column(String(50), nullable=False)
    base_unit_name: Mapped[str] = mapped_column(String(50), nullable=True)
    units_per_base: Mapped[float] = mapped_column(Double, nullable=True)

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
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

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
    bundle_items = relationship(
        "BundleItem",
        foreign_keys="BundleItem.bundle_product_id",
        cascade="all, delete-orphan",
    )
    category: Mapped["ProductCategory"] = relationship(
        "ProductCategory",
        back_populates="products"
    )

    ingredients: Mapped[list["ProductHasIngredient"]] = relationship(
        "ProductHasIngredient",
        back_populates="product",
        cascade="all, delete-orphan"
    )

class BundleItem(Base):
    """Componente de un paquete: vender el paquete descuenta cada componente.

    El paquete es un Product normal (tracks_batches=False: no tiene stock
    propio, su disponibilidad se deriva de los componentes). Los componentes
    pueden ser cualquier producto, incluidos los gemelos POS de animales.
    """

    __tablename__ = "bundle_items"
    __table_args__ = (
        UniqueConstraint("bundle_product_id", "component_product_id", name="uq_bundle_component"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bundle_product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    component = relationship("Product", foreign_keys=[component_product_id])
