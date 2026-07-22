"""Folio no secuencial (code) en pedidos

Revision ID: ordercode01
Revises: customerorders01
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ordercode01"
down_revision: Union[str, Sequence[str], None] = "customerorders01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("code", sa.String(length=20), nullable=True))

    # Backfill: los pedidos existentes reciben su folio PD-XXXXXXXX
    conn = op.get_bind()
    for (order_id,) in conn.execute(sa.text("SELECT id FROM orders WHERE code IS NULL")):
        conn.execute(
            sa.text("UPDATE orders SET code = :code WHERE id = :id"),
            {"code": f"PD-{uuid.uuid4().hex[:8].upper()}", "id": order_id},
        )

    op.alter_column("orders", "code", nullable=False)
    op.create_unique_constraint("uq_orders_code", "orders", ["code"])


def downgrade() -> None:
    op.drop_constraint("uq_orders_code", "orders", type_="unique")
    op.drop_column("orders", "code")
