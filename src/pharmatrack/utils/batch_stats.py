"""Conteos de lotes compartidos por /dashboard/stats y /stats/dashboard."""
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.product_batch.orm import ProductBatch


def expiring_soon_count(db: Session, today: date, days: int = 30) -> int:
    """Lotes con stock que vencen entre hoy y +days días."""
    return (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.expiration_date.between(today, today + timedelta(days=days)),
            ProductBatch.quantity > 0,
        )
        .scalar()
        or 0
    )


def expired_count(db: Session, today: date) -> int:
    """Lotes ya vencidos que aún tienen stock."""
    return (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.expiration_date < today,
            ProductBatch.quantity > 0,
        )
        .scalar()
        or 0
    )
