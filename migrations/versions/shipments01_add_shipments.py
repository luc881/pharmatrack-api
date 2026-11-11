"""Envíos sueltos (guías de Envia.com sin pedido del sitio)

Revision ID: shipments01
Revises: ordership01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "shipments01"
down_revision: Union[str, Sequence[str], None] = "ordership01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shipments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False, unique=True),
        sa.Column("note", sa.String(length=250), nullable=True),
        sa.Column("recipient_name", sa.String(length=255), nullable=False),
        sa.Column("recipient_phone", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("content", sa.String(length=100), nullable=False),
        sa.Column("carrier", sa.String(length=40), nullable=True),
        sa.Column("service", sa.String(length=60), nullable=True),
        sa.Column("tracking_number", sa.String(length=60), nullable=True),
        sa.Column("tracking_url", sa.String(length=500), nullable=True),
        sa.Column("label_url", sa.String(length=500), nullable=True),
        sa.Column("cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("shipments")
