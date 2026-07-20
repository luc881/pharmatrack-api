from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.products.orm import Product, BundleItem
from ..models.product_batch.orm import ProductBatch
from ..models.sale_batch_usage.orm import SaleBatchUsage
from ..models.sale_details.orm import SaleDetail


def expand_bundle_product_ids(db: Session, product_ids: list[int]) -> list[int]:
    """Ids efectivos de una venta: los paquetes se sustituyen por sus componentes.

    Lo usan la verificación de animales reservados y el marcado de vendidos
    en complete_sale — un animal dentro de un paquete cuenta igual que uno
    vendido directo.
    """
    effective: set[int] = set()
    for pid in product_ids:
        components = db.query(BundleItem.component_product_id).filter(
            BundleItem.bundle_product_id == pid
        ).all()
        if components:
            effective.update(c[0] for c in components)
        else:
            effective.add(pid)
    return list(effective)


def allocate_batches_for_sale_detail(
    db: Session,
    sale_detail: SaleDetail,
) -> None:
    """
    Assigns stock for a sale_detail.

    Queries the DB directly for pre-assigned SaleBatchUsage records so the
    result is independent of how the caller loaded the sale_detail object.
    If records exist → validate and deduct from those specific batches.
    If none exist → automatic FEFO allocation.
    """
    product = db.get(Product, sale_detail.product_id)

    # Paquete: no tiene stock propio — se descuenta cada componente
    # (cantidad del paquete × cantidad del componente). La trazabilidad
    # (SaleBatchUsage) queda ligada al detalle del paquete.
    bundle_items = (
        db.query(BundleItem)
        .filter(BundleItem.bundle_product_id == sale_detail.product_id)
        .all()
    )
    if bundle_items:
        for item in bundle_items:
            component = db.get(Product, item.component_product_id)
            if component is not None and not component.tracks_batches:
                continue  # componente de venta libre: nada que descontar
            _fefo_allocate(
                db,
                sale_detail,
                product_id=item.component_product_id,
                quantity=sale_detail.quantity * item.quantity,
                label=component.title if component else None,
            )
        return

    # Venta libre: productos sin control de lotes (granel por peso, servicios)
    # se cobran sin validar ni descontar stock — la caja de corteza no lleva
    # inventario, solo se pesa y se cobra por gramo
    if product is not None and not product.tracks_batches:
        return

    preassigned = (
        db.query(SaleBatchUsage)
        .filter(SaleBatchUsage.sale_detail_id == sale_detail.id)
        .all()
    )

    if preassigned:
        _apply_preassigned_usages(db, sale_detail, preassigned)
    else:
        _fefo_allocate(db, sale_detail)


def _product_label(sale_detail: SaleDetail) -> str:
    """Returns a human-readable product name for error messages."""
    try:
        return sale_detail.product.title
    except Exception:
        return f"producto {sale_detail.product_id}"


def _apply_preassigned_usages(
    db: Session,
    sale_detail: SaleDetail,
    usages: list[SaleBatchUsage],
) -> None:
    """Validates and deducts stock from batches already chosen by the frontend."""
    total_assigned = sum(u.quantity_used for u in usages)
    required = int(sale_detail.quantity)

    if total_assigned != required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Las cantidades pre-asignadas ({total_assigned}) no coinciden con "
                f"la cantidad solicitada ({required}) para {_product_label(sale_detail)}"
            ),
        )

    for usage in usages:
        batch = (
            db.query(ProductBatch)
            .filter(ProductBatch.id == usage.batch_id)
            .with_for_update()
            .first()
        )
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lote {usage.batch_id} no encontrado",
            )
        if batch.quantity < usage.quantity_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock insuficiente para {_product_label(sale_detail)} "
                    f"(lote {usage.batch_id}: disponible {batch.quantity}, requerido {usage.quantity_used})"
                ),
            )
        batch.quantity -= usage.quantity_used


def _fefo_allocate(
    db: Session,
    sale_detail: SaleDetail,
    product_id: int | None = None,
    quantity: Decimal | None = None,
    label: str | None = None,
) -> None:
    """
    FEFO automatic allocation.

    Batches are consumed in expiration_date ASC order (soonest-to-expire first).
    Batches with expiration_date=NULL (no-expiry stock) are placed last so
    dated stock is always consumed before undated stock. Within the same date,
    lower batch id wins (insertion order).

    product_id/quantity permiten asignar contra OTRO producto (componentes de
    un paquete) manteniendo la trazabilidad en el mismo sale_detail.
    """
    target_product_id = product_id if product_id is not None else sale_detail.product_id
    remaining_qty = quantity if quantity is not None else sale_detail.quantity
    error_label = label or _product_label(sale_detail)

    batches = (
        db.query(ProductBatch)
        .filter(
            ProductBatch.product_id == target_product_id,
            ProductBatch.quantity > 0,
        )
        .order_by(
            ProductBatch.expiration_date.asc().nullslast(),
            ProductBatch.id.asc(),
        )
        .with_for_update()
        .all()
    )

    if not batches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente para {error_label}",
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
            detail=f"Stock insuficiente para {error_label}",
        )
