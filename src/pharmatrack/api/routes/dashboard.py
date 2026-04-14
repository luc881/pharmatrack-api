from datetime import date, timedelta

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated, Optional

from ...db.session import get_db
from fastapi import Depends
from ...models.sales.orm import Sale
from ...models.users.orm import User
from ...models.products.orm import Product
from ...models.product_batch.orm import ProductBatch
from ...utils.permissions import CAN_READ_SALES
from ...utils.rate_limit import limiter, LIMIT_READ

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RecentSale(BaseModel):
    id: int
    date_sale: str
    total: float
    status: str
    user_name: Optional[str] = None


class ExpiringBatch(BaseModel):
    id: int
    expiration_date: date
    quantity: int
    product_title: Optional[str] = None


class DashboardSummary(BaseModel):
    monthly_sales_count: int
    monthly_revenue: float
    total_products: int
    expiring_batches_count: int
    expired_batches_count: int
    recent_sales: list[RecentSale]
    expiring_batches: list[ExpiringBatch]


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=DashboardSummary,
    summary="Dashboard summary stats",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
async def get_dashboard_summary(request: Request, db: db_dependency):
    today = date.today()
    first_of_month = today.replace(day=1)
    in_30_days = today + timedelta(days=30)

    # ── Ventas del mes actual ─────────────────────────────────────────────────
    monthly = (
        db.query(
            func.count(Sale.id).label("count"),
            func.coalesce(func.sum(Sale.total), 0).label("revenue"),
        )
        .filter(
            Sale.status == "completed",
            Sale.date_sale >= first_of_month,
        )
        .first()
    )

    # ── Total de productos activos ────────────────────────────────────────────
    total_products: int = (
        db.query(func.count(Product.id))
        .filter(Product.is_active == True, Product.deleted_at.is_(None))
        .scalar()
        or 0
    )

    # ── Lotes por vencer (hoy → +30 días, quantity > 0) ──────────────────────
    expiring_count: int = (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.expiration_date.between(today, in_30_days),
            ProductBatch.quantity > 0,
        )
        .scalar()
        or 0
    )

    # ── Lotes vencidos (quantity > 0) ────────────────────────────────────────
    expired_count: int = (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.expiration_date < today,
            ProductBatch.quantity > 0,
        )
        .scalar()
        or 0
    )

    # ── Últimas 10 ventas con nombre del usuario ──────────────────────────────
    recent_rows = (
        db.query(Sale, User.name.label("user_name"))
        .outerjoin(User, User.id == Sale.user_id)
        .order_by(Sale.date_sale.desc())
        .limit(10)
        .all()
    )

    recent_sales = [
        RecentSale(
            id=sale.id,
            date_sale=sale.date_sale.isoformat(),
            total=float(sale.total),
            status=sale.status,
            user_name=user_name,
        )
        for sale, user_name in recent_rows
    ]

    # ── 8 lotes más próximos a vencer con nombre de producto ─────────────────
    expiring_rows = (
        db.query(ProductBatch, Product.title.label("product_title"))
        .join(Product, Product.id == ProductBatch.product_id)
        .filter(
            ProductBatch.expiration_date.between(today, in_30_days),
            ProductBatch.quantity > 0,
        )
        .order_by(ProductBatch.expiration_date.asc())
        .limit(8)
        .all()
    )

    expiring_batches = [
        ExpiringBatch(
            id=batch.id,
            expiration_date=batch.expiration_date,
            quantity=batch.quantity,
            product_title=product_title,
        )
        for batch, product_title in expiring_rows
    ]

    return DashboardSummary(
        monthly_sales_count=monthly.count,
        monthly_revenue=float(monthly.revenue),
        total_products=total_products,
        expiring_batches_count=expiring_count,
        expired_batches_count=expired_count,
        recent_sales=recent_sales,
        expiring_batches=expiring_batches,
    )
