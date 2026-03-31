from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated

from ...db.session import get_db
from ...models.sales.orm import Sale
from ...models.sale_details.orm import SaleDetail
from ...models.sale_payments.orm import SalePayment
from ...models.products.orm import Product
from ...models.product_batch.orm import ProductBatch
from ...utils.permissions import CAN_READ_SALES
from ...utils.rate_limit import limiter, LIMIT_READ

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/stats", tags=["Stats"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class MonthStat(BaseModel):
    month: str
    revenue: float
    count: int


class ProductStat(BaseModel):
    product_id: int
    title: str
    quantity_sold: float
    revenue: float


class PaymentStat(BaseModel):
    method: str
    count: int
    total: float


class MonthComparison(BaseModel):
    revenue: float
    count: int


class MonthlyComparison(BaseModel):
    current_month: MonthComparison
    previous_month: MonthComparison


class DashboardStats(BaseModel):
    sales_by_month: list[MonthStat]
    top_products: list[ProductStat]
    payment_methods: list[PaymentStat]
    monthly_comparison: MonthlyComparison
    expiring_soon: int
    low_stock_batches: int


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Dashboard statistics",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
async def get_dashboard_stats(request: Request, db: db_dependency):
    today = date.today()

    # ── sales_by_month ────────────────────────────────────────────────────────
    first_of_twelve_months_ago = (today.replace(day=1) - timedelta(days=365))

    sales_by_month_rows = (
        db.query(
            func.to_char(Sale.date_sale, "YYYY-MM").label("month"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("count"),
        )
        .filter(
            Sale.status == "completed",
            Sale.date_sale >= first_of_twelve_months_ago,
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    sales_by_month = [
        MonthStat(month=r.month, revenue=float(r.revenue), count=r.count)
        for r in sales_by_month_rows
    ]

    # ── top_products ──────────────────────────────────────────────────────────
    top_rows = (
        db.query(
            SaleDetail.product_id,
            Product.title,
            func.sum(SaleDetail.quantity).label("quantity_sold"),
            func.sum(
                SaleDetail.quantity * func.coalesce(Product.price_retail, 0)
            ).label("revenue"),
        )
        .join(Product, Product.id == SaleDetail.product_id)
        .group_by(SaleDetail.product_id, Product.title)
        .order_by(func.sum(SaleDetail.quantity).desc())
        .limit(10)
        .all()
    )

    top_products = [
        ProductStat(
            product_id=r.product_id,
            title=r.title,
            quantity_sold=float(r.quantity_sold),
            revenue=float(r.revenue),
        )
        for r in top_rows
    ]

    # ── payment_methods ───────────────────────────────────────────────────────
    payment_rows = (
        db.query(
            SalePayment.method_payment.label("method"),
            func.count(SalePayment.id).label("count"),
            func.sum(SalePayment.amount).label("total"),
        )
        .group_by(SalePayment.method_payment)
        .all()
    )

    payment_methods = [
        PaymentStat(method=r.method, count=r.count, total=float(r.total))
        for r in payment_rows
    ]

    # ── monthly_comparison ────────────────────────────────────────────────────
    first_current = today.replace(day=1)
    first_previous = (first_current - timedelta(days=1)).replace(day=1)

    def _month_stats(start: date, end: date) -> MonthComparison:
        row = (
            db.query(
                func.coalesce(func.sum(Sale.total), 0).label("revenue"),
                func.count(Sale.id).label("count"),
            )
            .filter(
                Sale.status == "completed",
                Sale.date_sale >= start,
                Sale.date_sale < end,
            )
            .first()
        )
        return MonthComparison(revenue=float(row.revenue), count=row.count)

    monthly_comparison = MonthlyComparison(
        current_month=_month_stats(first_current, today),
        previous_month=_month_stats(first_previous, first_current),
    )

    # ── expiring_soon ─────────────────────────────────────────────────────────
    in_30_days = today + timedelta(days=30)

    expiring_soon: int = (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.expiration_date.between(today, in_30_days),
            ProductBatch.quantity > 0,
        )
        .scalar()
        or 0
    )

    # ── low_stock_batches ─────────────────────────────────────────────────────
    low_stock_batches: int = (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.quantity > 0,
            ProductBatch.quantity <= 10,
        )
        .scalar()
        or 0
    )

    return DashboardStats(
        sales_by_month=sales_by_month,
        top_products=top_products,
        payment_methods=payment_methods,
        monthly_comparison=monthly_comparison,
        expiring_soon=expiring_soon,
        low_stock_batches=low_stock_batches,
    )
