"""Bandera show_in_nav en grupos de animales

Revision ID: groupshowinnav01
Revises: customeraddress01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "groupshowinnav01"
down_revision: Union[str, Sequence[str], None] = "customeraddress01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Por defecto en 1: los grupos que ya estaban en el menu siguen ahi
    op.add_column("animal_groups", sa.Column("show_in_nav", sa.Boolean(),
                                             server_default="1", nullable=False))


def downgrade() -> None:
    op.drop_column("animal_groups", "show_in_nav")
