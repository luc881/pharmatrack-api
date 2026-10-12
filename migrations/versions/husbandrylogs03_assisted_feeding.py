"""Bitácora: alimentación asistida (forzada)

Revision ID: husbandrylogs03
Revises: purchasestock01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "husbandrylogs03"
down_revision: Union[str, Sequence[str], None] = "purchasestock01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "husbandry_logs",
        sa.Column("assisted", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_husbandry_logs_animal_id", "husbandry_logs", ["animal_id"])


def downgrade() -> None:
    op.drop_index("ix_husbandry_logs_animal_id", table_name="husbandry_logs")
    op.drop_column("husbandry_logs", "assisted")
