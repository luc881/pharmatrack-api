from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

from possystem.models.products.schemas import PaginatedResponse, PaginationParams


# =========================================================
# 🔹 Base
# =========================================================
class PermissionBase(BaseModel):
    name: str = Field(..., max_length=255, min_length=1, description="Permission name")

    model_config = dict(from_attributes=True)

    @field_validator("name")
    @classmethod
    def strip_lower_and_validate(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"^[a-z.]+$", v):
            raise ValueError("Invalid permission name pattern, only lowercase letters and '.' are allowed")
        return v


# =========================================================
# 🟢 Create
# =========================================================
class PermissionCreate(PermissionBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "edit_users"
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class PermissionUpdate(PermissionBase):
    name: Optional[str] = Field(None, max_length=255, min_length=1, description="Permission name")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "edit_users_updated"
            }
        }
    )


# =========================================================
# 🔵 Response
# =========================================================
class PermissionResponse(PermissionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "edit_users",
                "created_at": "2024-06-01T12:34:56",
                "updated_at": "2024-06-02T10:00:00"
            }
        }
    )


# =========================================================
# 🧩 Response con roles
# =========================================================
class PermissionWithRoles(PermissionResponse):
    roles: List["RoleResponse"] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "edit_users",
                "created_at": "2024-06-01T12:34:56",
                "updated_at": "2024-06-02T10:00:00",
                "roles": [
                    {
                        "id": 1,
                        "name": "admin",
                        "created_at": "2024-06-01T12:34:56",
                        "updated_at": "2024-06-02T10:00:00"
                    }
                ]
            }
        }
    )


# =========================================================
# 🔁 Forward references
# =========================================================
if TYPE_CHECKING:
    from ..roles.schemas import RoleResponse


# =========================================================
# 🔁 Re-exportar para uso en el router
# =========================================================
__all__ = [
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionWithRoles",
    "PaginatedResponse",
    "PaginationParams",
]