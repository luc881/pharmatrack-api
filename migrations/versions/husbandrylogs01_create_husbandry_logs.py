"""Bitácora del plan de manejo de especies

Revision ID: husbandrylogs01
Revises: taxonimage01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "husbandrylogs01"
down_revision: Union[str, Sequence[str], None] = "taxonimage01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "husbandry_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("species_id", sa.BigInteger(), nullable=False),
        sa.Column("morph_id", sa.BigInteger(), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("fed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("food_type", sa.String(length=100), nullable=True),
        sa.Column("pieces", sa.Integer(), nullable=True),
        sa.Column("grams", sa.Numeric(8, 2), nullable=True),
        sa.Column("appetite", sa.String(length=20), nullable=True),
        sa.Column("feeding_notes", sa.Text(), nullable=True),
        sa.Column("activities", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["morph_id"], ["morphs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_husbandry_logs_species_id", "husbandry_logs", ["species_id"])
    op.create_index("ix_husbandry_logs_log_date", "husbandry_logs", ["log_date"])


def downgrade() -> None:
    op.drop_index("ix_husbandry_logs_log_date", table_name="husbandry_logs")
    op.drop_index("ix_husbandry_logs_species_id", table_name="husbandry_logs")
    op.drop_table("husbandry_logs")
