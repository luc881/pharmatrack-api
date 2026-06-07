"""add tracks_batches to products and make expiration_date nullable in product_batches

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-06-06

- products.tracks_batches (Boolean, NOT NULL, default TRUE)
  All existing products default to TRUE — no behaviour change.
- product_batches.expiration_date becomes nullable so that products with
  tracks_batches=False can have a "stock bucket" batch without an expiry date.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3b4c5d6e7f8'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column(
            'tracks_batches',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
    )
    op.alter_column(
        'product_batches',
        'expiration_date',
        existing_type=sa.Date(),
        nullable=True,
    )


def downgrade() -> None:
    # Restore NOT NULL — set a placeholder date for any rows that have NULL
    op.execute(
        "UPDATE product_batches SET expiration_date = CURRENT_DATE WHERE expiration_date IS NULL"
    )
    op.alter_column(
        'product_batches',
        'expiration_date',
        existing_type=sa.Date(),
        nullable=False,
    )
    op.drop_column('products', 'tracks_batches')
