"""Llave de idempotencia en ventas (POST /sales/checkout)

Revision ID: saleidem01
Revises: animals08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "saleidem01"
down_revision: Union[str, Sequence[str], None] = "animals08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_sales_idempotency_key", "sales", ["idempotency_key"])


def downgrade() -> None:
    op.drop_constraint("uq_sales_idempotency_key", "sales", type_="unique")
    op.drop_column("sales", "idempotency_key")
