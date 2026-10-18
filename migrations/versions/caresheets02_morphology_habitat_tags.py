"""Fichas de cuidados: morfología, hábitat y etiquetas

Revision ID: caresheets02
Revises: caresheets01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "caresheets02"
down_revision: Union[str, Sequence[str], None] = "caresheets01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("care_sheets", sa.Column("morphology", sa.JSON(), nullable=True))
    op.add_column("care_sheets", sa.Column("habitat", sa.Text(), nullable=True))
    op.add_column("care_sheets", sa.Column("tags", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("care_sheets", "tags")
    op.drop_column("care_sheets", "habitat")
    op.drop_column("care_sheets", "morphology")
