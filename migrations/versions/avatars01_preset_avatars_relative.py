"""Avatares predefinidos como ruta, sin dominio

Revision ID: avatars01
Revises: levels01

Los avatares predefinidos del dashboard se guardaban con el dominio del momento
(https://app.farmaciaselene.com/assets/...) y se rompieron al cambiar de dominio.
Ahora se guardan como ruta (/assets/images/mock/avatar/avatar-N.webp).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "avatars01"
down_revision: Union[str, Sequence[str], None] = "levels01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        r"""
        UPDATE users
        SET avatar = regexp_replace(avatar, '^https?://[^/]+(/assets/images/mock/avatar/)', '\1')
        WHERE avatar ~ '^https?://[^/]+/assets/images/mock/avatar/avatar-[0-9]+\.webp$'
        """
    )


def downgrade() -> None:
    # ponytail: sin vuelta atrás; la ruta sirve en cualquier dominio
    pass
