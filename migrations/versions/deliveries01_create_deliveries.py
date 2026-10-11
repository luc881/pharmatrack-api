"""Control de entregas (ventas y cambios en persona)

Revision ID: deliveries01
Revises: husbandrylogs02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "deliveries01"
down_revision: Union[str, Sequence[str], None] = "husbandrylogs02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deliveries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("kind", sa.String(length=10), server_default="sale", nullable=False),
        sa.Column("status", sa.String(length=12), server_default="pending", nullable=False),
        sa.Column("buyer_name", sa.String(length=150), nullable=False),
        sa.Column("buyer_contact", sa.String(length=150), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.String(length=5), nullable=True),
        sa.Column("place", sa.String(length=200), nullable=True),
        sa.Column("items_given", sa.JSON(), nullable=False),
        sa.Column("items_received", sa.JSON(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("paid", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("payment_method", sa.String(length=10), nullable=True),
        sa.Column("sale_id", sa.BigInteger(), nullable=True),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deliveries_status", "deliveries", ["status"])
    op.create_index("ix_deliveries_scheduled_date", "deliveries", ["scheduled_date"])


def downgrade() -> None:
    op.drop_index("ix_deliveries_scheduled_date", table_name="deliveries")
    op.drop_index("ix_deliveries_status", table_name="deliveries")
    op.drop_table("deliveries")
