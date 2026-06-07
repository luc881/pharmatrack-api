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
from ...models.sale_batch_usage.orm import SaleBatchUsage
from ...models.products.orm import Product
from ...models.product_batch.orm import ProductBatch
from ...models.product_categories.orm import ProductCategory
from ...models.branches.orm import Branch
from ...utils.permissions import CAN_READ_DASHBOARD
from ...utils.rate_limit import limiter, LIMIT_READ
from pharmatrack.types.sales import SaleStatusEnum

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/stats", tags=["Stats"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class MonthStat(BaseModel):
    month: str
    revenue: float
    count: int
    cost: float
    profit: float


class ProductStat(BaseModel):
    product_id: int
    title: str
    quantity_sold: float
    revenue: float
    cost: float
    profit: float


class PaymentStat(BaseModel):
    method: str
    count: int
    total: float


class MonthComparison(BaseModel):
    revenue: float
    count: int
    cost: float
    profit: float


class MonthlyComparison(BaseModel):
    current_month: MonthComparison
    previous_month: MonthComparison


class CategoryStat(BaseModel):
    category: str
    revenue: float
    count: int


class BranchStat(BaseModel):
    branch: str
    revenue: float
    count: int


class DashboardStats(BaseModel):
    sales_by_month: list[MonthStat]
    top_products: list[ProductStat]
    payment_methods: list[PaymentStat]
    monthly_comparison: MonthlyComparison
    expiring_soon: int
    low_stock_batches: int
    expired_batches: int
    sales_by_category: list[CategoryStat]
    sales_by_branch: list[BranchStat]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cost_expr():
    """SQLAlchemy expression: quantity_used × purchase_price (NULL-safe)."""
    return SaleBatchUsage.quantity_used * func.coalesce(ProductBatch.purchase_price, 0)


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Dashboard statistics",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_DASHBOARD,
)
@limiter.limit(LIMIT_READ)
async def get_dashboard_stats(request: Request, db: db_dependency):
    today = date.today()

    # ── sales_by_month ────────────────────────────────────────────────────────
    first_of_twelve_months_ago = today.replace(day=1) - timedelta(days=365)

    sales_by_month_rows = (
        db.query(
            func.to_char(Sale.date_sale, "YYYY-MM").label("month"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("count"),
        )
        .filter(
            Sale.status == SaleStatusEnum.COMPLETED,
            Sale.date_sale >= first_of_twelve_months_ago,
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    # Cost per month via separate query to avoid double-counting Sale.total
    cost_by_month_rows = (
        db.query(
            func.to_char(Sale.date_sale, "YYYY-MM").label("month"),
            func.coalesce(func.sum(_cost_expr()), 0).label("cost"),
        )
        .join(SaleDetail, SaleDetail.sale_id == Sale.id)
        .join(SaleBatchUsage, SaleBatchUsage.sale_detail_id == SaleDetail.id)
        .join(ProductBatch, ProductBatch.id == SaleBatchUsage.batch_id)
        .filter(
            Sale.status == SaleStatusEnum.COMPLETED,
            Sale.date_sale >= first_of_twelve_months_ago,
        )
        .group_by("month")
        .all()
    )
    cost_by_month: dict[str, float] = {r.month: float(r.cost) for r in cost_by_month_rows}

    sales_by_month = [
        MonthStat(
            month=r.month,
            revenue=float(r.revenue),
            count=r.count,
            cost=cost_by_month.get(r.month, 0.0),
            profit=float(r.revenue) - cost_by_month.get(r.month, 0.0),
        )
        for r in sales_by_month_rows
    ]

    # ── top_products ──────────────────────────────────────────────────────────
    top_rows = (
        db.query(
            SaleDetail.product_id,
            Product.title,
            func.sum(SaleDetail.quantity).label("quantity_sold"),
            func.sum(SaleDetail.total).label("revenue"),
        )
        .join(Product, Product.id == SaleDetail.product_id)
        .group_by(SaleDetail.product_id, Product.title)
        .order_by(func.sum(SaleDetail.quantity).desc())
        .limit(10)
        .all()
    )

    # Cost per product via separate query
    cost_by_product_rows = (
        db.query(
            SaleDetail.product_id,
            func.coalesce(func.sum(_cost_expr()), 0).label("cost"),
        )
        .join(SaleBatchUsage, SaleBatchUsage.sale_detail_id == SaleDetail.id)
        .join(ProductBatch, ProductBatch.id == SaleBatchUsage.batch_id)
        .group_by(SaleDetail.product_id)
        .all()
    )
    cost_by_product: dict[int, float] = {r.product_id: float(r.cost) for r in cost_by_product_rows}

    top_products = [
        ProductStat(
            product_id=r.product_id,
            title=r.title,
            quantity_sold=float(r.quantity_sold),
            revenue=float(r.revenue),
            cost=cost_by_product.get(r.product_id, 0.0),
            profit=float(r.revenue) - cost_by_product.get(r.product_id, 0.0),
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

    def _month_cost(start: date, end: date) -> float:
        row = (
            db.query(func.coalesce(func.sum(_cost_expr()), 0).label("cost"))
            .join(SaleDetail, SaleDetail.id == SaleBatchUsage.sale_detail_id)
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .join(ProductBatch, ProductBatch.id == SaleBatchUsage.batch_id)
            .filter(
                Sale.status == SaleStatusEnum.COMPLETED,
                Sale.date_sale >= start,
                Sale.date_sale < end,
            )
            .first()
        )
        return float(row.cost) if row else 0.0

    def _month_stats(start: date, end: date) -> MonthComparison:
        row = (
            db.query(
                func.coalesce(func.sum(Sale.total), 0).label("revenue"),
                func.count(Sale.id).label("count"),
            )
            .filter(
                Sale.status == SaleStatusEnum.COMPLETED,
                Sale.date_sale >= start,
                Sale.date_sale < end,
            )
            .first()
        )
        revenue = float(row.revenue)
        cost = _month_cost(start, end)
        return MonthComparison(revenue=revenue, count=row.count, cost=cost, profit=revenue - cost)

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

    # ── expired_batches ───────────────────────────────────────────────────────
    expired_batches: int = (
        db.query(func.count(ProductBatch.id))
        .filter(
            ProductBatch.expiration_date < today,
            ProductBatch.expiration_date.isnot(None),
            ProductBatch.quantity > 0,
        )
        .scalar()
        or 0
    )

    # ── sales_by_category ─────────────────────────────────────────────────────
    sales_by_category_rows = (
        db.query(
            ProductCategory.name.label("category"),
            func.sum(SaleDetail.total).label("revenue"),
            func.count(func.distinct(Sale.id)).label("count"),
        )
        .join(Sale, Sale.id == SaleDetail.sale_id)
        .join(Product, Product.id == SaleDetail.product_id)
        .join(ProductCategory, ProductCategory.id == Product.product_category_id)
        .filter(
            Sale.status == SaleStatusEnum.COMPLETED,
            Sale.date_sale >= first_of_twelve_months_ago,
        )
        .group_by(ProductCategory.name)
        .order_by(func.sum(SaleDetail.total).desc())
        .all()
    )

    sales_by_category = [
        CategoryStat(category=r.category, revenue=float(r.revenue), count=r.count)
        for r in sales_by_category_rows
    ]

    # ── sales_by_branch ───────────────────────────────────────────────────────
    sales_by_branch_rows = (
        db.query(
            Branch.name.label("branch"),
            func.sum(Sale.total).label("revenue"),
            func.count(Sale.id).label("count"),
        )
        .join(Branch, Branch.id == Sale.branch_id)
        .filter(
            Sale.status == SaleStatusEnum.COMPLETED,
            Sale.date_sale >= first_of_twelve_months_ago,
        )
        .group_by(Branch.name)
        .order_by(func.sum(Sale.total).desc())
        .all()
    )

    sales_by_branch = [
        BranchStat(branch=r.branch, revenue=float(r.revenue), count=r.count)
        for r in sales_by_branch_rows
    ]

    return DashboardStats(
        sales_by_month=sales_by_month,
        top_products=top_products,
        payment_methods=payment_methods,
        monthly_comparison=monthly_comparison,
        expiring_soon=expiring_soon,
        low_stock_batches=low_stock_batches,
        expired_batches=expired_batches,
        sales_by_category=sales_by_category,
        sales_by_branch=sales_by_branch,
    )
