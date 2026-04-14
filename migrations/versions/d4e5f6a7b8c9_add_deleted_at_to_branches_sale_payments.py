"""add deleted_at to branches and sale_payments

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("branches",     sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True))
    op.add_column("sale_payments", sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column("sale_payments", "deleted_at")
    op.drop_column("branches",      "deleted_at")
