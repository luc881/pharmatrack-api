"""Plan de manejo por especie; suplementos, bajas y fotos en la bitácora

Revision ID: husbandrylogs02
Revises: husbandrylogs01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "husbandrylogs02"
down_revision: Union[str, Sequence[str], None] = "husbandrylogs01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("species", sa.Column("husbandry_plan", sa.JSON(), nullable=True))
    op.add_column("husbandry_logs", sa.Column("supplement", sa.String(length=100), nullable=True))
    op.add_column("husbandry_logs", sa.Column("deaths", sa.Integer(), nullable=True))
    op.add_column("husbandry_logs", sa.Column("animal_id", sa.BigInteger(), nullable=True))
    op.add_column("husbandry_logs", sa.Column("stock_deducted", sa.Integer(), server_default="0", nullable=False))
    op.add_column("husbandry_logs", sa.Column("photos", sa.JSON(), nullable=True))
    op.create_foreign_key(
        "fk_husbandry_logs_animal_id", "husbandry_logs", "animals", ["animal_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_husbandry_logs_animal_id", "husbandry_logs", type_="foreignkey")
    for col in ("photos", "stock_deducted", "animal_id", "deaths", "supplement"):
        op.drop_column("husbandry_logs", col)
    op.drop_column("species", "husbandry_plan")
