from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.product_batch.orm import ProductBatch
from ..models.sale_batch_usage.orm import SaleBatchUsage
from ..models.sale_details.orm import SaleDetail


def allocate_batches_for_sale_detail(
    db: Session,
    sale_detail: SaleDetail,
) -> None:
    """
    Assigns stock for a sale_detail.

    If the frontend already pre-assigned batch usages (via POST /sale-batch-usages/),
    those are validated and stock is deducted from the named batches.
    Otherwise falls back to automatic FEFO allocation.
    """
    # Lazy-load is fine here; batch_usages is a list relationship on SaleDetail
    if sale_detail.batch_usages:
        _apply_preassigned_usages(db, sale_detail)
    else:
        _fefo_allocate(db, sale_detail)


def _apply_preassigned_usages(db: Session, sale_detail: SaleDetail) -> None:
    """Validates and deducts stock from batches already chosen by the frontend."""
    total_assigned = sum(u.quantity_used for u in sale_detail.batch_usages)
    required = int(sale_detail.quantity)

    if total_assigned != required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Pre-assigned batch quantities ({total_assigned}) do not match "
                f"sale detail quantity ({required}) for product {sale_detail.product_id}"
            ),
        )

    for usage in sale_detail.batch_usages:
        batch = (
            db.query(ProductBatch)
            .filter(ProductBatch.id == usage.batch_id)
            .with_for_update()
            .first()
        )
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch {usage.batch_id} not found",
            )
        if batch.quantity < usage.quantity_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock in batch {usage.batch_id} "
                    f"(available: {batch.quantity}, required: {usage.quantity_used})"
                ),
            )
        batch.quantity -= usage.quantity_used


def _fefo_allocate(db: Session, sale_detail: SaleDetail) -> None:
    """Automatic FEFO allocation when no batch usages are pre-assigned."""
    remaining_qty = sale_detail.quantity

    batches = (
        db.query(ProductBatch)
        .filter(
            ProductBatch.product_id == sale_detail.product_id,
            ProductBatch.quantity > 0,
        )
        .order_by(
            ProductBatch.expiration_date.asc(),
            ProductBatch.id.asc(),
        )
        .with_for_update()
        .all()
    )

    if not batches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No stock available for product {sale_detail.product_id}",
        )

    for batch in batches:
        if remaining_qty <= 0:
            break

        usable_qty = min(Decimal(str(batch.quantity)), remaining_qty)

        db.add(SaleBatchUsage(
            sale_detail_id=sale_detail.id,
            batch_id=batch.id,
            quantity_used=int(usable_qty),
        ))

        batch.quantity -= int(usable_qty)
        remaining_qty -= usable_qty

    if remaining_qty > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for product {sale_detail.product_id}",
        )
