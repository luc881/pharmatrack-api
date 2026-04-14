"""add deleted_at to users, roles and products

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users",   sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True))
    op.add_column("roles",   sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True))
    op.add_column("products", sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "deleted_at")
    op.drop_column("roles",    "deleted_at")
    op.drop_column("users",    "deleted_at")
