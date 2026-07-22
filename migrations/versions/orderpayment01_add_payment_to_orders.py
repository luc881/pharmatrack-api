"""Pago en linea y metodo de entrega en pedidos

Revision ID: orderpayment01
Revises: ordercode01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "orderpayment01"
down_revision: Union[str, Sequence[str], None] = "ordercode01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("delivery_method", sa.String(length=20),
                                      server_default="shipping", nullable=False))
    op.add_column("orders", sa.Column("payment_id", sa.String(length=50), nullable=True))
    op.add_column("orders", sa.Column("paid_at", sa.TIMESTAMP(), nullable=True))
    op.create_index("ix_orders_payment_id", "orders", ["payment_id"])


def downgrade() -> None:
    op.drop_index("ix_orders_payment_id", table_name="orders")
    op.drop_column("orders", "paid_at")
    op.drop_column("orders", "payment_id")
    op.drop_column("orders", "delivery_method")
