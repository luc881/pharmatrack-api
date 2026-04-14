from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session, joinedload
from starlette import status
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func
from pharmatrack.types.sales import SaleStatusEnum

from ...db.session import get_db
from ...models.refund_products.orm import RefundProduct
from ...models.refund_products.schemas import RefundProductCreate, RefundProductResponse, RefundProductUpdate
from ...models.products.orm import Product
from ...models.sale_details.orm import SaleDetail
from ...models.users.orm import User
from ...models.product_batch.orm import ProductBatch
from ...models.sales.orm import Sale
from ...utils.permissions import CAN_READ_REFUND_PRODUCTS, CAN_CREATE_REFUND_PRODUCTS, CAN_UPDATE_REFUND_PRODUCTS, \
    CAN_DELETE_REFUND_PRODUCTS

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/refundproducts",
    tags=["Refund Products"]
)


# -----------------------
# FUNCIÓN AUXILIAR: Validar cantidad máxima de refund
# -----------------------
def validate_max_refund_quantity(db: Session, sale_detail_id: int, refund_id_to_exclude: int = None,
                                 new_quantity: float = None) -> tuple[SaleDetail, float]:
    """
    Valida que la cantidad a refundir no supere la cantidad original de la venta.
    Retorna: (sale_detail, cantidad_disponible_para_refund)
    """
    sale_detail = db.query(SaleDetail).filter(SaleDetail.id == sale_detail_id).first()
    if not sale_detail:
        raise HTTPException(status_code=404, detail="Sale detail not found")

    # Obtener todos los refunds existentes para este sale_detail
    query = db.query(func.sum(RefundProduct.quantity)).filter(
        RefundProduct.sale_detail_id == sale_detail_id
    )

    # Excluir el refund actual si se está actualizando
    if refund_id_to_exclude:
        query = query.filter(RefundProduct.id != refund_id_to_exclude)

    total_refunded = query.scalar() or 0.0

    # Calcular cantidad disponible para refund
    available_for_refund = float(sale_detail.quantity) - total_refunded

    if new_quantity is not None and new_quantity > available_for_refund:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot refund {new_quantity} units. Only {available_for_refund:.2f} units available from sale (original: {sale_detail.quantity}, already refunded: {total_refunded:.2f})"
        )

    return sale_detail, available_for_refund


# -----------------------
# FUNCIÓN AUXILIAR: Actualizar estado de la venta
# -----------------------
def update_sale_status_after_refund(db: Session, sale_detail_id: int):
    """
    Actualiza automáticamente el estado de la venta después de un refund.
    - Si el total refundido = total original → "refunded"
    - Si el total refundido > 0 pero < total original → "partially_refunded"
    - Si no hay refunds → mantener estado original (completed)
    """
    # Obtener el sale_detail y la venta asociada
    sale_detail = db.query(SaleDetail).filter(SaleDetail.id == sale_detail_id).first()
    if not sale_detail:
        return None

    sale = db.query(Sale).filter(Sale.id == sale_detail.sale_id).first()
    if not sale:
        return None

    # Solo procesar si la venta está en estado "completed" o "partially_refunded"
    if sale.status not in (SaleStatusEnum.COMPLETED, SaleStatusEnum.PARTIALLY_REFUNDED, SaleStatusEnum.REFUNDED):
        return sale

    # Obtener todos los sale_details de esta venta
    all_sale_details = db.query(SaleDetail).filter(SaleDetail.sale_id == sale.id).all()

    # Variables para determinar el estado
    all_fully_refunded = True
    any_partially_refunded = False
    all_not_refunded = True

    # Calcular refunds por cada sale_detail de la venta
    for sd in all_sale_details:
        # Obtener total refundido para este sale_detail
        total_refunded = db.query(func.sum(RefundProduct.quantity)).filter(
            RefundProduct.sale_detail_id == sd.id
        ).scalar() or 0.0

        original_quantity = float(sd.quantity)

        # Determinar estado por producto
        if total_refunded == 0:
            all_fully_refunded = False
        elif total_refunded < original_quantity:
            all_fully_refunded = False
            any_partially_refunded = True
            all_not_refunded = False
        elif total_refunded == original_quantity:
            any_partially_refunded = True
            all_not_refunded = False

    # Determinar estado final de la venta
    if all_not_refunded:
        new_status = SaleStatusEnum.COMPLETED
    elif all_fully_refunded:
        new_status = SaleStatusEnum.REFUNDED
    elif any_partially_refunded:
        new_status = SaleStatusEnum.PARTIALLY_REFUNDED
    else:
        new_status = sale.status  # Mantener estado actual

    # Actualizar solo si cambió el estado
    if sale.status != new_status:
        sale.status = new_status
        db.add(sale)

    return sale


# -----------------------
# GET ALL
# -----------------------
@router.get(
    "",
    response_model=list[RefundProductResponse],
    summary="List all refund products",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_REFUND_PRODUCTS
)
async def read_all(db: db_dependency):
    return db.query(RefundProduct).all()


# -----------------------
# CREATE
# -----------------------
@router.post(
    "",
    response_model=RefundProductResponse,
    summary="Create a new refund product",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_REFUND_PRODUCTS
)
async def create(refund_product: RefundProductCreate, db: db_dependency):
    # Validar producto
    product = db.query(Product).filter(Product.id == refund_product.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Associated product not found")

    # Validar sale detail si se proporciona
    sale_detail = None
    if refund_product.sale_detail_id:
        sale_detail = db.query(SaleDetail).options(joinedload(SaleDetail.batch_usages)).filter(
            SaleDetail.id == refund_product.sale_detail_id
        ).first()
        if not sale_detail:
            raise HTTPException(status_code=404, detail="Associated sale detail not found")

    # Validar usuario si se proporciona
    if refund_product.user_id:
        user = db.query(User).filter(User.id == refund_product.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Associated user not found")

    # VALIDACIÓN CRÍTICA: No superar cantidad original de la venta
    if sale_detail:
        validate_max_refund_quantity(db, sale_detail.id, None, float(refund_product.quantity))

    new_refund = RefundProduct(**refund_product.model_dump())

    # -----------------------
    # Reintegrar stock a lotes originales de forma parcial
    # -----------------------
    reintegrated_batches = {}
    if refund_product.is_reintegrable and sale_detail:
        remaining_qty = refund_product.quantity

        # Ordenamos los lotes por fecha de expiración (FEFO)
        batch_usages = sorted(sale_detail.batch_usages, key=lambda x: x.id)

        for usage in batch_usages:
            if remaining_qty <= 0:
                break

            batch = db.query(ProductBatch).filter(ProductBatch.id == usage.batch_id).with_for_update().first()
            if not batch:
                continue

            # Cantidad que se puede reintegrar de este lote
            reintegrate_qty = min(usage.quantity_used, remaining_qty)
            if reintegrate_qty > 0:
                batch.quantity += reintegrate_qty
                reintegrated_batches[str(batch.id)] = reintegrate_qty
                remaining_qty -= reintegrate_qty

        if remaining_qty > 0:
            # Si intentas reintegrar más de lo vendido en la venta original
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reintegrate {refund_product.quantity} units. Only {refund_product.quantity - remaining_qty} available from sale."
            )

    # Guardamos los lotes reintegrados en el refund
    new_refund.reintegrated_batches = reintegrated_batches

    db.add(new_refund)
    db.commit()

    # -----------------------
    # ACTUALIZAR ESTADO DE LA VENTA
    # -----------------------
    if sale_detail:
        update_sale_status_after_refund(db, sale_detail.id)
        db.commit()

    db.refresh(new_refund)
    return new_refund


# -----------------------
# UPDATE
# -----------------------
@router.put(
    "/{id}",
    response_model=RefundProductResponse,
    summary="Update an existing refund product",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_REFUND_PRODUCTS
)
async def update(id: int, refund_product: RefundProductUpdate, db: db_dependency):
    existing_refund = db.query(RefundProduct).filter(RefundProduct.id == id).first()
    if not existing_refund:
        raise HTTPException(status_code=404, detail="Refund product not found")

    # Validaciones
    if refund_product.product_id:
        product = db.query(Product).filter(Product.id == refund_product.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Associated product not found")

    # Cargar el sale_detail del refund existente
    sale_detail = None
    if existing_refund.sale_detail_id:
        sale_detail = db.query(SaleDetail).options(joinedload(SaleDetail.batch_usages)).filter(
            SaleDetail.id == existing_refund.sale_detail_id
        ).first()
        if not sale_detail:
            raise HTTPException(status_code=404, detail="Associated sale detail not found")

    # Si se proporciona un nuevo sale_detail_id, validarlo
    if refund_product.sale_detail_id and refund_product.sale_detail_id != existing_refund.sale_detail_id:
        new_sale_detail = db.query(SaleDetail).options(joinedload(SaleDetail.batch_usages)).filter(
            SaleDetail.id == refund_product.sale_detail_id
        ).first()
        if not new_sale_detail:
            raise HTTPException(status_code=404, detail="New sale detail not found")
        sale_detail = new_sale_detail

    if refund_product.user_id:
        user = db.query(User).filter(User.id == refund_product.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Associated user not found")

    # -----------------------
    # VALIDACIÓN CRÍTICA: No superar cantidad original de la venta
    # -----------------------
    update_data = refund_product.model_dump(exclude_unset=True)

    if 'quantity' in update_data and sale_detail:
        # Validar que la nueva cantidad no supere lo disponible
        validate_max_refund_quantity(db, sale_detail.id, id, float(refund_product.quantity))

    # -----------------------
    # Manejo de reintegros parciales en update
    # -----------------------
    # Solo procesar cambios en quantity si el refund es reintegrable y tiene sale_detail
    if sale_detail and 'quantity' in update_data and existing_refund.is_reintegrable:
        old_qty = existing_refund.quantity
        new_qty = refund_product.quantity
        delta = new_qty - old_qty

        reintegrated_batches = dict(existing_refund.reintegrated_batches or {})

        # Ordenamos lotes por id (FEFO)
        batch_usages = sorted(sale_detail.batch_usages, key=lambda x: x.id)

        if delta > 0:  # Aumentar refund → reintegrar stock
            remaining_qty = delta
            for usage in batch_usages:
                if remaining_qty <= 0:
                    break
                batch = db.query(ProductBatch).filter(ProductBatch.id == usage.batch_id).with_for_update().first()
                if not batch:
                    continue
                already_reintegrated = reintegrated_batches.get(str(batch.id), 0)
                can_reintegrate = usage.quantity_used - already_reintegrated
                reintegrate_qty = min(can_reintegrate, remaining_qty)
                if reintegrate_qty <= 0:
                    continue
                batch.quantity += reintegrate_qty
                reintegrated_batches[str(batch.id)] = already_reintegrated + reintegrate_qty
                remaining_qty -= reintegrate_qty

            if remaining_qty > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reintegrate additional {delta} units. Only {delta - remaining_qty} available from sale."
                )

        elif delta < 0:  # Reducir refund → quitar stock reintegrado
            remaining_qty = -delta
            for usage in batch_usages:
                if remaining_qty <= 0:
                    break
                batch = db.query(ProductBatch).filter(ProductBatch.id == usage.batch_id).with_for_update().first()
                if not batch:
                    continue
                already_reintegrated = reintegrated_batches.get(str(batch.id), 0)
                revert_qty = min(already_reintegrated, remaining_qty)
                if revert_qty <= 0:
                    continue
                batch.quantity -= revert_qty
                reintegrated_batches[str(batch.id)] = already_reintegrated - revert_qty
                remaining_qty -= revert_qty

            if remaining_qty > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot remove {-delta} units from stock. Only {-delta - remaining_qty} were previously reintegrated."
                )

        # CRÍTICO: Actualizar y marcar como modificado
        existing_refund.reintegrated_batches = reintegrated_batches
        flag_modified(existing_refund, "reintegrated_batches")

    # -----------------------
    # Aplicar cambios restantes del update
    # -----------------------
    for key, value in update_data.items():
        setattr(existing_refund, key, value)

    db.commit()

    # -----------------------
    # ACTUALIZAR ESTADO DE LA VENTA
    # -----------------------
    if sale_detail:
        update_sale_status_after_refund(db, sale_detail.id)
        db.commit()

    db.refresh(existing_refund)
    return existing_refund


# -----------------------
# DELETE
# -----------------------
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a refund product",
    dependencies=CAN_DELETE_REFUND_PRODUCTS
)
async def delete(id: int, db: db_dependency):
    existing_refund = db.query(RefundProduct).filter(RefundProduct.id == id).first()
    if not existing_refund:
        raise HTTPException(status_code=404, detail="Refund product not found")

    # Guardar sale_detail_id antes de borrar para actualizar el estado de la venta
    sale_detail_id = existing_refund.sale_detail_id

    # Si el refund es reintegrable, debemos revertir el stock
    if existing_refund.is_reintegrable and existing_refund.reintegrated_batches:
        sale_detail = db.query(SaleDetail).options(joinedload(SaleDetail.batch_usages)).filter(
            SaleDetail.id == existing_refund.sale_detail_id
        ).first()

        if sale_detail:
            # Revertir el stock de los lotes
            for batch_id_str, qty in existing_refund.reintegrated_batches.items():
                batch_id = int(batch_id_str)
                batch = db.query(ProductBatch).filter(ProductBatch.id == batch_id).with_for_update().first()
                if batch:
                    batch.quantity -= qty

    # Borrado físico
    db.delete(existing_refund)
    db.commit()

    # -----------------------
    # ACTUALIZAR ESTADO DE LA VENTA
    # -----------------------
    if sale_detail_id:
        update_sale_status_after_refund(db, sale_detail_id)
        db.commit()

    return