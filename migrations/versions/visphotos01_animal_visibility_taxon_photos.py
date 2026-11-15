"""Ejemplar fuera del sitio y varias fotos por especie y variedad

Revision ID: visphotos01
Revises: varietymode01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "visphotos01"
down_revision: Union[str, Sequence[str], None] = "varietymode01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("animals", sa.Column("show_public", sa.Boolean(), nullable=False, server_default=sa.true()))
    for table in ("species", "morphs"):
        op.add_column(table, sa.Column("photos", sa.JSON(), nullable=False, server_default="[]"))
        # la foto que ya tenían pasa a ser la primera (y principal)
        op.execute(
            f"UPDATE {table} SET photos = json_build_array(image) "
            f"WHERE image IS NOT NULL AND image <> ''"
        )


def downgrade() -> None:
    op.drop_column("morphs", "photos")
    op.drop_column("species", "photos")
    op.drop_column("animals", "show_public")
