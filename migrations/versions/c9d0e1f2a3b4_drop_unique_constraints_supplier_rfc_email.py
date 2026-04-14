"""drop unique constraints on supplier rfc and email

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-14

Removes DB-level UNIQUE constraints on suppliers.rfc and suppliers.email.
Uniqueness is enforced at application level, allowing future soft-delete
without blocking re-registration of the same RFC/email.

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c9d0e1f2a3b4'
down_revision = 'b8c9d0e1f2a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("suppliers_email_key", "suppliers", type_="unique")
    op.drop_constraint("suppliers_rfc_key", "suppliers", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("suppliers_email_key", "suppliers", ["email"])
    op.create_unique_constraint("suppliers_rfc_key", "suppliers", ["rfc"])
