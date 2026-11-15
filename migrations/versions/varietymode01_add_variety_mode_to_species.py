"""Especies: tipo de variedades (con nombre / genes combinables)

Revision ID: varietymode01
Revises: convextras01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "varietymode01"
down_revision: Union[str, Sequence[str], None] = "convextras01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "species",
        sa.Column("variety_mode", sa.String(20), nullable=False, server_default="named"),
    )
    # Lo que ya existe no se rompe: una especie con algún ejemplar de dos o
    # más morphs ya se maneja por combinación
    op.execute("""
        UPDATE species SET variety_mode = 'genes'
        WHERE id IN (
            SELECT a.species_id
            FROM animals a
            JOIN animal_has_morphs ahm ON ahm.animal_id = a.id
            GROUP BY a.id, a.species_id
            HAVING COUNT(*) > 1
        )
    """)


def downgrade() -> None:
    op.drop_column("species", "variety_mode")
