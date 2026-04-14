"""add indexes on sales.status and sale_payments.method_payment

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-04-14

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd0e1f2a3b4c5'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_sales_status", "sales", ["status"])
    op.create_index("ix_sale_payments_method_payment", "sale_payments", ["method_payment"])


def downgrade() -> None:
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_index("ix_sale_payments_method_payment", table_name="sale_payments")
