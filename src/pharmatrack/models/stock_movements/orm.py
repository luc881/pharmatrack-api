"""Historial de movimientos de stock.

Cada cambio en `product_batches.quantity` deja una fila: cuánto cambió, cuánto
quedó, quién lo hizo y desde qué ruta. Se registra solo, en un listener de la
sesión, así que cubre ventas, devoluciones, compras, bitácora y ajustes a mano
sin tocar cada ruta. No lo ven los UPDATE masivos (`query.update`) ni los
borrados en cascada de la BD.
"""
from contextvars import ContextVar
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Integer, String, TIMESTAMP, event, insert
from sqlalchemy.orm import Mapped, Session, attributes, mapped_column
from sqlalchemy.sql import func

from ...db.session import Base
from ..product_batch.orm import ProductBatch

# (user_id, "MÉTODO /ruta") de la petición en curso; lo pone decode_jwt_token.
# Fuera de una petición de staff (seeds, scripts) queda en (None, None).
actor: ContextVar[tuple[Optional[int], Optional[str]]] = ContextVar("stock_actor", default=(None, None))


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Sin llave foránea a propósito: el historial sobrevive al lote borrado
    batch_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


@event.listens_for(Session, "after_flush")
def _record_stock_movements(session, flush_context):
    # after_flush: los lotes nuevos ya tienen id y el historial de atributos
    # todavía no se limpia
    rows = []

    def add(batch, old, new):
        delta = int(new or 0) - int(old or 0)
        if delta:
            rows.append({"batch_id": batch.id, "product_id": batch.product_id,
                         "delta": delta, "quantity_after": int(new or 0)})

    for obj in session.new:
        if isinstance(obj, ProductBatch):
            add(obj, 0, obj.quantity)
    for obj in session.dirty:
        if isinstance(obj, ProductBatch):
            old = attributes.get_history(obj, "quantity").deleted
            if old:
                add(obj, old[0], obj.quantity)
    for obj in session.deleted:
        if isinstance(obj, ProductBatch):
            add(obj, obj.quantity, 0)

    if rows:
        user_id, source = actor.get()
        for row in rows:
            row.update(user_id=user_id, source=source)
        session.execute(insert(StockMovement.__table__), rows)
