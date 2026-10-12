"""Bitácora: estado previo a la baja y cambio por otro ejemplar

Revision ID: husbandrylogs05
Revises: husbandrylogs04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "husbandrylogs05"
down_revision: Union[str, Sequence[str], None] = "husbandrylogs04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("husbandry_logs", sa.Column("prev_status", sa.String(length=20), nullable=True))
    op.add_column("husbandry_logs", sa.Column("replacement_animal_id", sa.BigInteger(), nullable=True))
    op.add_column("husbandry_logs", sa.Column("replaced_usage_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_husbandry_logs_replacement_animal_id", "husbandry_logs", "animals",
        ["replacement_animal_id"], ["id"], ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_husbandry_logs_replaced_usage_id", "husbandry_logs", "sale_batch_usages",
        ["replaced_usage_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_husbandry_logs_replaced_usage_id", "husbandry_logs", type_="foreignkey")
    op.drop_constraint("fk_husbandry_logs_replacement_animal_id", "husbandry_logs", type_="foreignkey")
    op.drop_column("husbandry_logs", "replaced_usage_id")
    op.drop_column("husbandry_logs", "replacement_animal_id")
    op.drop_column("husbandry_logs", "prev_status")
