"""add enum types for user gender and document type

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-14

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE documenttypeenum AS ENUM ('INE', 'PASSPORT', 'LICENSE')"
    )
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN type_document TYPE documenttypeenum "
        "USING type_document::documenttypeenum"
    )

    op.execute(
        "CREATE TYPE genderenum AS ENUM ('M', 'F')"
    )
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN gender TYPE genderenum "
        "USING gender::genderenum"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN type_document TYPE VARCHAR(50) "
        "USING type_document::VARCHAR"
    )
    op.execute("DROP TYPE documenttypeenum")

    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN gender TYPE VARCHAR(5) "
        "USING gender::VARCHAR"
    )
    op.execute("DROP TYPE genderenum")
