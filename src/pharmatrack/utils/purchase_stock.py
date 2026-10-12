from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.products.orm import Product
from ..models.product_batch.orm import ProductBatch
from ..models.purchase_details.orm import PurchaseDetail


def stock_in(db: Session, detail: PurchaseDetail) -> None:
    """Suma al stock lo que llegó en un renglón de compra.

    Mismo criterio que POST /productsbatches: con lot_code se suma a ese lote
    (o se crea); sin lote, al lote con la misma caducidad (sin caducidad = el
    lote «stock» canónico). Deja detail.batch_id para poder deshacerlo.
    Venta libre (tracks_batches=False) no lleva inventario: no toca nada.
    """
    product = db.get(Product, detail.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    detail.batch_id = None
    if not product.tracks_batches:
        return

    qty = float(detail.quantity)
    if not qty.is_integer():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La cantidad de «{product.title}» debe ser entera: su inventario va por pieza.",
        )

    query = db.query(ProductBatch).filter(ProductBatch.product_id == product.id)
    if detail.lot_code:
        query = query.filter(ProductBatch.lot_code == detail.lot_code)
    else:
        query = query.filter(
            ProductBatch.lot_code.is_(None),
            ProductBatch.expiration_date == detail.expiration_date
            if detail.expiration_date
            else ProductBatch.expiration_date.is_(None),
        )
    batch = query.with_for_update().first()

    if batch:
        batch.quantity += int(qty)
    else:
        batch = ProductBatch(
            product_id=product.id,
            lot_code=detail.lot_code or None,
            expiration_date=detail.expiration_date,
            quantity=int(qty),
        )
        db.add(batch)
        db.flush()
    batch.purchase_price = float(detail.unit_price)
    detail.batch_id = batch.id


def stock_out(db: Session, details: list[PurchaseDetail]) -> None:
    """Resta del stock lo que esos renglones habían sumado (para editar o borrar).

    Si de algún lote ya se vendió más de lo que queda, no toca nada y avisa:
    hay que ajustar en Stock y lotes primero. Renglones viejos sin batch_id
    nunca sumaron stock, así que no restan.
    """
    need: dict[int, int] = defaultdict(int)
    for d in details:
        if d.batch_id:
            need[d.batch_id] += int(float(d.quantity))

    batches = {
        b.id: b
        for b in db.query(ProductBatch).filter(ProductBatch.id.in_(need)).with_for_update()
    }
    for batch_id, qty in need.items():
        batch = batches.get(batch_id)
        if batch and batch.quantity < qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Ya se vendió parte de «{batch.product.title}» de esta compra "
                    f"(quedan {batch.quantity} de {qty}). Ajusta ese lote en "
                    "Stock y lotes antes de cambiar o borrar la compra."
                ),
            )

    for batch_id, qty in need.items():
        batch = batches.get(batch_id)
        if not batch:
            continue  # el lote se borró a mano: nada que restar
        batch.quantity -= qty
        if batch.quantity == 0 and not batch.sale_usages:
            db.delete(batch)
    # antes de volver a sumar: un lote recreado con el mismo lot_code chocaría
    # con el borrado si el DELETE se manda después del INSERT
    db.flush()
