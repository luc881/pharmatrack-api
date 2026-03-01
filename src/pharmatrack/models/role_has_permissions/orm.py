from sqlalchemy import Table, Column, ForeignKey, BigInteger
from ...db.session import Base

role_has_permissions = Table(
    "role_has_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)