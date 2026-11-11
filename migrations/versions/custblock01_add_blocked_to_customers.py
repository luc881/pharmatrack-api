"""Bloqueo de clientes que abusan de los pedidos

Revision ID: custblock01
Revises: shipments01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "custblock01"
down_revision: Union[str, Sequence[str], None] = "shipments01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("blocked", sa.Boolean(), nullable=False,
                                         server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("customers", "blocked")
