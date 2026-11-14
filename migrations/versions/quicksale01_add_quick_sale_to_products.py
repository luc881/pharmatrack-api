"""Bandera de venta rapida en productos

Revision ID: quicksale01
Revises: orderip01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "quicksale01"
down_revision: Union[str, Sequence[str], None] = "orderip01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("quick_sale", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("products", "quick_sale")
