"""Destino del animal (venta, pie de cría, crianza)

Revision ID: animals08
Revises: caresheets02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "animals08"
down_revision: Union[str, Sequence[str], None] = "caresheets02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("animals", sa.Column("purpose", sa.String(20), nullable=False, server_default="sale"))
    op.create_index("ix_animals_purpose", "animals", ["purpose"])


def downgrade() -> None:
    op.drop_index("ix_animals_purpose", table_name="animals")
    op.drop_column("animals", "purpose")
