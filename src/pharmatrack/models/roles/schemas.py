from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams


# =========================================================
# 🔹 Base
# =========================================================
class RoleBase(BaseModel):
    name: str = Field(..., max_length=255, min_length=1, description="Role name")

    @field_validator("name")
    @classmethod
    def strip_lower_and_validate(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"^[a-zA-Z0-9._\- áéíóúüñÁÉÍÓÚÜÑ]+$", v):
            raise ValueError("Role name may only contain letters (including accented), numbers, spaces, dots, hyphens and underscores")
        return v


# =========================================================
# 🟢 Create
# =========================================================
class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = Field(default=[], description="List of permission IDs to assign to this role")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "admin",
                "permission_ids": [1, 2, 3]
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class RoleUpdate(RoleBase):
    name: Optional[str] = Field(None, max_length=255, min_length=1, description="Role name")
    permission_ids: Optional[List[int]] = Field(None, description="List of permission IDs to assign to this role")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "admin_updated",
                "permission_ids": [1, 2, 4]
            }
        }
    )


# =========================================================
# 🔵 Response
# =========================================================
class RoleResponse(RoleBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "admin",
                "created_at": "2024-06-01T12:34:56",
                "updated_at": "2024-06-02T10:00:00"
            }
        }
    )


# =========================================================
# 🧩 Response con permisos
# =========================================================
class RoleWithPermissions(RoleResponse):
    permissions: List["PermissionResponse"] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "admin",
                "created_at": "2024-06-01T12:34:56",
                "updated_at": "2024-06-02T10:00:00",
                "permissions": [
                    {
                        "id": 1,
                        "name": "edit_users",
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
    from ..permissions.schemas import PermissionResponse


# =========================================================
# 🔁 Re-exportar para uso en el router
# =========================================================
__all__ = [
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    "PaginatedResponse",
    "PaginationParams",
]