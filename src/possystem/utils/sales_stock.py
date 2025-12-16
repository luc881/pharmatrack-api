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
    Asigna stock por lotes (FEFO) para un sale_detail.
    Crea SaleBatchUsage y descuenta stock.
    """

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

        usable_qty = min(batch.quantity, remaining_qty)

        usage = SaleBatchUsage(
            sale_detail_id=sale_detail.id,
            batch_id=batch.id,
            quantity_used=usable_qty,
        )

        db.add(usage)

        batch.quantity -= usable_qty
        remaining_qty -= usable_qty

    if remaining_qty > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for product {sale_detail.product_id}",
        )
