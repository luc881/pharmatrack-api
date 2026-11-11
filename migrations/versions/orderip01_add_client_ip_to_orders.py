"""IP del visitante en pedidos (tope diario por red)

Revision ID: orderip01
Revises: custblock01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "orderip01"
down_revision: Union[str, Sequence[str], None] = "custblock01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("client_ip", sa.String(length=45), nullable=True))
    op.create_index("ix_orders_client_ip", "orders", ["client_ip"])


def downgrade() -> None:
    op.drop_index("ix_orders_client_ip", table_name="orders")
    op.drop_column("orders", "client_ip")
