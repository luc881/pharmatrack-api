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
from ...models.products.orm import Product
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
    # None = venta libre (sin control de stock, p. ej. granel por peso)
    stock: Optional[int] = Field(None, description="Unidades disponibles; None si es venta libre")

    model_config = ConfigDict(from_attributes=True)


def _to_public(product: Product, stock) -> PublicProductResponse:
    return PublicProductResponse(
        id=product.id,
        title=product.title,
        price_retail=product.price_retail,
        image=product.image,
        description=product.description,
        unit_name=product.unit_name,
        is_unit_sale=product.is_unit_sale,
        tracks_batches=product.tracks_batches,
        category=product.category.name if product.category else None,
        stock=int(stock) if product.tracks_batches else None,
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

    return [_to_public(product, stock) for product, stock in rows]


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
    return _to_public(product, _stock_of(db, product_id))
