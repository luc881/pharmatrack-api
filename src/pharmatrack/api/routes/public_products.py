"""Catálogo público de productos (insumos de terrario, etc.).

Solo productos activos con show_online=True — el resto del catálogo
interno (farmacia, gemelos de animales) jamás se expone.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import Field, BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from ...db.session import db_dependency
from ...models.products.orm import Product, BundleItem
from ...models.product_batch.orm import ProductBatch

router = APIRouter(prefix="/public/products", tags=["Public"])


class PublicProductResponse(BaseModel):
    """Vista pública: sin costos ni campos internos."""

    id: int
    title: str
    price_retail: float
    image: Optional[str] = None
    description: Optional[str] = None
    unit_name: Optional[str] = None
    is_unit_sale: bool = True
    tracks_batches: bool = True
    # Nombre de la subcategoría (Sustratos, Decoración…) para el menú lateral
    category: Optional[str] = None
    # Precio anterior (tachado) para mostrar la oferta
    compare_at_price: Optional[float] = None
    # None = venta libre (sin control de stock, p. ej. granel por peso)
    stock: Optional[int] = Field(None, description="Unidades disponibles; None si es venta libre")
    # Paquete: componentes incluidos (título y cantidad)
    is_bundle: bool = False
    components: list["PublicBundleComponent"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PublicBundleComponent(BaseModel):
    product_id: int
    title: str
    quantity: int
    image: Optional[str] = None


def _bundle_stock(db, items) -> Optional[int]:
    """Disponibilidad derivada: el mínimo entre componentes con stock."""
    available = None
    for item in items:
        component = db.get(Product, item.component_product_id)
        if component is None or not component.tracks_batches:
            continue  # los de venta libre no limitan
        comp_stock = _stock_of(db, item.component_product_id) or 0
        can_make = int(comp_stock) // item.quantity
        available = can_make if available is None else min(available, can_make)
    return available


def _to_public(db, product: Product, stock) -> PublicProductResponse:
    items = (
        db.query(BundleItem)
        .options(selectinload(BundleItem.component))
        .filter(BundleItem.bundle_product_id == product.id)
        .all()
    )

    if items:
        effective_stock = _bundle_stock(db, items)
        tracks = effective_stock is not None
    else:
        effective_stock = int(stock) if product.tracks_batches else None
        tracks = product.tracks_batches

    return PublicProductResponse(
        id=product.id,
        title=product.title,
        price_retail=product.price_retail,
        compare_at_price=product.compare_at_price,
        image=product.image,
        description=product.description,
        unit_name=product.unit_name,
        is_unit_sale=product.is_unit_sale,
        tracks_batches=tracks,
        category=product.category.name if product.category else None,
        stock=effective_stock,
        is_bundle=bool(items),
        components=[
            PublicBundleComponent(
                product_id=item.component_product_id,
                title=item.component.title if item.component else f"Producto {item.component_product_id}",
                quantity=item.quantity,
                image=item.component.image if item.component else None,
            )
            for item in items
        ],
    )


def _stock_of(db, product_id: int):
    return (
        db.query(func.coalesce(func.sum(ProductBatch.quantity), 0))
        .filter(ProductBatch.product_id == product_id)
        .scalar()
    )


@router.get("", response_model=list[PublicProductResponse],
            summary="Productos visibles en el sitio público")
async def public_list_products(db: db_dependency):
    rows = (
        db.query(Product, func.coalesce(func.sum(ProductBatch.quantity), 0))
        .outerjoin(ProductBatch, ProductBatch.product_id == Product.id)
        # selectinload: joinedload rompe el GROUP BY del agregado de stock
        .options(selectinload(Product.category))
        .filter(
            Product.deleted_at.is_(None),
            Product.is_active.is_(True),
            Product.show_online.is_(True),
        )
        .group_by(Product.id)
        .order_by(Product.title)
        .all()
    )

    return [_to_public(db, product, stock) for product, stock in rows]


@router.get("/{product_id}", response_model=PublicProductResponse,
            summary="Detalle público de un producto")
async def public_get_product(product_id: int, db: db_dependency):
    product = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(
            Product.id == product_id,
            Product.deleted_at.is_(None),
            Product.is_active.is_(True),
            Product.show_online.is_(True),
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return _to_public(db, product, _stock_of(db, product_id))
