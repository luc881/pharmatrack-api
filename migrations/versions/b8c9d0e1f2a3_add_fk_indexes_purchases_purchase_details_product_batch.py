"""add FK indexes on purchases, purchase_details, product_batch

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-04-14

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_purchases_supplier_id", "purchases", ["supplier_id"])
    op.create_index("ix_purchases_user_id", "purchases", ["user_id"])
    op.create_index("ix_purchase_details_purchase_id", "purchase_details", ["purchase_id"])
    op.create_index("ix_purchase_details_product_id", "purchase_details", ["product_id"])
    op.create_index("ix_product_batches_product_id", "product_batches", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_purchases_supplier_id", table_name="purchases")
    op.drop_index("ix_purchases_user_id", table_name="purchases")
    op.drop_index("ix_purchase_details_purchase_id", table_name="purchase_details")
    op.drop_index("ix_purchase_details_product_id", table_name="purchase_details")
    op.drop_index("ix_product_batches_product_id", table_name="product_batches")
