"""Guía de envío en pedidos (Envia.com)

Revision ID: ordership01
Revises: stockmov01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ordership01"
down_revision: Union[str, Sequence[str], None] = "stockmov01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = (
    ("shipping_carrier", sa.String(length=40)),
    ("shipping_service", sa.String(length=60)),
    ("tracking_number", sa.String(length=60)),
    ("tracking_url", sa.String(length=500)),
    ("label_url", sa.String(length=500)),
    ("shipping_cost", sa.Numeric(12, 2)),
)


def upgrade() -> None:
    for name, kind in COLUMNS:
        op.add_column("orders", sa.Column(name, kind, nullable=True))


def downgrade() -> None:
    for name, _kind in reversed(COLUMNS):
        op.drop_column("orders", name)
