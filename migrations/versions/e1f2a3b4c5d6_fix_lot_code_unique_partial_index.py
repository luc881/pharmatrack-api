"""fix lot_code unique constraint to partial index (WHERE lot_code IS NOT NULL)

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-04-14

Replaces the standard UNIQUE constraint on (product_id, lot_code) with a
partial unique index that only applies when lot_code IS NOT NULL.
This allows multiple batches of the same product without a lot_code (NULL),
while still preventing duplicate non-null lot_codes per product.

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_product_lot_code", "product_batches", type_="unique")
    op.execute(
        "CREATE UNIQUE INDEX uq_product_lot_code_notnull "
        "ON product_batches (product_id, lot_code) "
        "WHERE lot_code IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_product_lot_code_notnull")
    op.create_unique_constraint(
        "uq_product_lot_code", "product_batches", ["product_id", "lot_code"]
    )
