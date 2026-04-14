from typing import Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator, HttpUrl, SecretStr

from pharmatrack.types.users import NameStr, SurnameStr, MXPhoneNumber, NumDocStr, DocumentTypeEnum, GenderEnum
from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams


# =========================================================
# 🔹 Base
# =========================================================
class UserBase(BaseModel):
    name: NameStr = Field(..., description="Nombre del usuario")
    surname: Optional[SurnameStr] = Field(None, description="Apellido del usuario")
    email: EmailStr = Field(..., max_length=255, description="Correo electrónico")
    avatar: Optional[HttpUrl] = Field(None, max_length=255, description="URL del avatar del usuario")
    branch_id: Optional[int] = Field(None, gt=0, description="ID de la sucursal")
    phone: Optional[MXPhoneNumber] = Field(None, description="Número telefónico en formato E164")
    type_document: Optional[DocumentTypeEnum] = Field(None, description="Tipo de documento")
    n_document: Optional[NumDocStr] = Field(None, description="Número de documento")
    gender: Optional[GenderEnum] = Field(None, description="Género (M/F)")
    role_id: Optional[int] = Field(None, gt=0, description="ID del rol asignado")

    model_config = dict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def strip_all_strings(cls, values):
        if not isinstance(values, dict):
            values = vars(values)
        clean = {}
        for key, value in values.items():
            if isinstance(value, str):
                clean[key] = value.strip()
            else:
                clean[key] = value
        return clean


# =========================================================
# 🟢 Create
# =========================================================
class UserCreate(UserBase):
    password: SecretStr = Field(..., min_length=8, max_length=255, description="Contraseña del usuario")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: SecretStr):
        pwd = v.get_secret_value()
        if len(pwd) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in pwd):
            raise ValueError("Debe contener al menos una mayúscula.")
        if not any(c.isdigit() for c in pwd):
            raise ValueError("Debe contener al menos un número.")
        return v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Juan",
                "surname": "Pérez",
                "email": "juan.perez@example.com",
                "password": "securepassword123",
                "avatar": "http://example.com/avatar.jpg",
                "phone": "5551234567",
                "type_document": "INE",
                "n_document": "ABC123456",
                "gender": "M",
                "branch_id": 1,
                "role_id": 2
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class UserUpdate(UserBase):
    name: Optional[NameStr] = Field(None, description="Nombre del usuario")
    email: Optional[EmailStr] = Field(None, max_length=255)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Juanito",
                "email": "juanito.perez@example.com",
            }
        }
    )


# =========================================================
# 🔵 Response
# =========================================================
class UserResponse(UserBase):
    id: int
    email_verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Juan",
                "surname": "Pérez",
                "email": "juan.perez@example.com",
                "email_verified_at": "2024-06-01T12:34:56",
                "avatar": "http://example.com/avatar.jpg",
                "phone": "5551234567",
                "type_document": "INE",
                "n_document": "ABC123456",
                "gender": "M",
                "created_at": "2024-06-01T12:00:00",
                "updated_at": "2024-06-02T10:00:00",
                "branch_id": None,
                "role_id": None
            }
        }
    )


# =========================================================
# 🧩 Detailed response
# =========================================================
class UserDetailsResponse(UserResponse):
    role: Optional["RoleWithPermissions"] = None
    branch: Optional["BranchResponse"] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Juan",
                "surname": "Pérez",
                "email": "juan.perez@example.com",
                "email_verified_at": "2024-06-01T12:34:56",
                "avatar": "http://example.com/avatar.jpg",
                "phone": "5551234567",
                "type_document": "INE",
                "n_document": "ABC123456",
                "gender": "M",
                "created_at": "2024-06-01T12:00:00",
                "updated_at": "2024-06-02T10:00:00",
                "branch": {
                    "id": 10,
                    "name": "Sucursal Centro",
                    "address": "Av. Principal 123, CDMX",
                    "is_active": True,
                    "created_at": "2024-07-01T10:15:00",
                    "updated_at": "2024-07-05T09:00:00",
                },
                "role": {
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
        }
    )


# =========================================================
# 🔍 Search params
# =========================================================
class UserSearchParams(BaseModel):
    name: Optional[NameStr] = Field(None, description="Filter by first name")
    surname: Optional[SurnameStr] = Field(None, description="Filter by surname")
    email: Optional[EmailStr] = Field(None, description="Filter by email")
    branch_id: Optional[int] = Field(None, gt=0, description="Filter by branch ID")
    role_id: Optional[int] = Field(None, gt=0, description="Filter by role ID")
    state: Optional[bool] = Field(None, description="Filter by active/inactive state")
    phone: Optional[str] = Field(None, description="Filter by phone number")
    gender: Optional[str] = Field(None, pattern=r"^(M|F)$", description="Filter by gender")
    type_document: Optional[str] = Field(None, description="Filter by document type")
    n_document: Optional[str] = Field(None, description="Filter by document number")

    @field_validator("name", "surname", "email", "type_document", "n_document", "phone", mode="before")
    def normalize_text(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("gender", mode="before")
    def normalize_gender(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v


# =========================================================
# 🔐 Change password
# =========================================================
class ChangePasswordRequest(BaseModel):
    old_password: SecretStr = Field(...)
    new_password: SecretStr = Field(...)

    @field_validator("new_password")
    def validate_new_password(cls, v: SecretStr):
        pwd = v.get_secret_value()
        if len(pwd) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in pwd):
            raise ValueError("Debe contener al menos una mayúscula.")
        if not any(c.isdigit() for c in pwd):
            raise ValueError("Debe contener al menos un número.")
        return v


# =========================================================
# 🔁 Forward references
# =========================================================
if TYPE_CHECKING:
    from ..roles.schemas import RoleWithPermissions
    from ..branches.schemas import BranchResponse


# =========================================================
# 🔁 Re-exportar para uso en el router
# =========================================================
__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserDetailsResponse",
    "UserSearchParams",
    "ChangePasswordRequest",
    "PaginatedResponse",
    "PaginationParams",
]