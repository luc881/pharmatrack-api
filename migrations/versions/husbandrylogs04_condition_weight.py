"""Bitácora: estado del ejemplar (activo, letárgico u otro) y peso

Revision ID: husbandrylogs04
Revises: husbandrylogs03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "husbandrylogs04"
down_revision: Union[str, Sequence[str], None] = "husbandrylogs03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("husbandry_logs", sa.Column("condition", sa.String(length=20), nullable=True))
    op.add_column("husbandry_logs", sa.Column("condition_note", sa.String(length=200), nullable=True))
    op.add_column("husbandry_logs", sa.Column("weight_g", sa.Numeric(8, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("husbandry_logs", "weight_g")
    op.drop_column("husbandry_logs", "condition_note")
    op.drop_column("husbandry_logs", "condition")
