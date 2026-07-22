"""Direccion estructurada del cliente

Revision ID: customeraddress01
Revises: orderpayment01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "customeraddress01"
down_revision: Union[str, Sequence[str], None] = "orderpayment01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNS = (
    ("street", sa.String(length=200)),
    ("ext_number", sa.String(length=20)),
    ("int_number", sa.String(length=20)),
    ("neighborhood", sa.String(length=150)),
    ("zip_code", sa.String(length=5)),
    ("city", sa.String(length=150)),
    ("state", sa.String(length=60)),
    ("address_notes", sa.Text()),
)


def upgrade() -> None:
    # `address` se conserva: sigue siendo el texto que copian pedidos y correos.
    # Las direcciones viejas quedan ahi hasta que el cliente llene el formulario.
    for name, kind in _COLUMNS:
        op.add_column("customers", sa.Column(name, kind, nullable=True))


def downgrade() -> None:
    for name, _kind in reversed(_COLUMNS):
        op.drop_column("customers", name)
