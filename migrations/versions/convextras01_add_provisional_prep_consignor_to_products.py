"""Productos: provisional, se prepara y de quien es

Revision ID: convextras01
Revises: quicksale01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "convextras01"
down_revision: Union[str, Sequence[str], None] = "quicksale01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("provisional", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("client_key", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_products_client_key", "products", ["client_key"])
    op.add_column("products", sa.Column("needs_prep", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("consignor_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key("fk_products_consignor", "products", "suppliers",
                          ["consignor_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_products_consignor", "products", type_="foreignkey")
    op.drop_column("products", "consignor_id")
    op.drop_column("products", "needs_prep")
    op.drop_constraint("uq_products_client_key", "products", type_="unique")
    op.drop_column("products", "client_key")
    op.drop_column("products", "provisional")
