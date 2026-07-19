"""Catálogo público de productos (insumos de terrario, etc.).

Solo productos activos con show_online=True — el resto del catálogo
interno (farmacia, gemelos de animales) jamás se expone.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import Field, BaseModel, ConfigDict
from sqlalchemy import func

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
    # None = venta libre (sin control de stock, p. ej. granel por peso)
    stock: Optional[int] = Field(None, description="Unidades disponibles; None si es venta libre")

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=list[PublicProductResponse],
            summary="Productos visibles en el sitio público")
async def public_list_products(db: db_dependency):
    rows = (
        db.query(Product, func.coalesce(func.sum(ProductBatch.quantity), 0))
        .outerjoin(ProductBatch, ProductBatch.product_id == Product.id)
        .filter(
            Product.deleted_at.is_(None),
            Product.is_active.is_(True),
            Product.show_online.is_(True),
        )
        .group_by(Product.id)
        .order_by(Product.title)
        .all()
    )

    result = []
    for product, stock in rows:
        item = PublicProductResponse.model_validate(product)
        item.stock = int(stock) if product.tracks_batches else None
        result.append(item)
    return result
