from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams
from pharmatrack.types.suppliers import SupplierNameStr, SupplierRFCStr, SupplierPhoneStr
from pharmatrack.utils.normalize import norm_title

__all__ = ["PaginatedResponse", "PaginationParams"]


# =========================================================
# 🔹 Base
# =========================================================
class SupplierBase(BaseModel):
    name: SupplierNameStr = Field(..., description="Nombre o razón social del proveedor")
    logo: Optional[str] = Field(None, max_length=255, description="URL del logo o imagen")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    phone: SupplierPhoneStr = Field(None, description="Teléfono de contacto")
    address: Optional[str] = Field(None, max_length=250, description="Dirección")
    rfc: Optional[SupplierRFCStr] = Field(None, description="RFC / identificación tributaria")
    is_active: bool = Field(True, description="Estado del proveedor")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return norm_title(v)


# =========================================================
# 🟢 Create
# =========================================================
class SupplierCreate(SupplierBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Distribuidora ABC S.A.",
                "logo": "https://example.com/logo.png",
                "email": "contacto@abc.com",
                "phone": "+52 555-123-4567",
                "address": "Av. Reforma 123, CDMX",
                "rfc": "ABC123456789",
                "is_active": True,
            }
        },
    )


# =========================================================
# 🟡 Update
# =========================================================
class SupplierUpdate(BaseModel):
    name: Optional[SupplierNameStr] = None
    logo: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: SupplierPhoneStr = None
    address: Optional[str] = Field(None, max_length=250)
    rfc: Optional[SupplierRFCStr] = None
    is_active: Optional[bool] = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v):
        return norm_title(v) if v is not None else v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Distribuidora ABC S.A. de C.V.",
                "phone": "+52 555-987-6543",
                "is_active": False,
            }
        },
    )


# =========================================================
# 🔵 Response
# =========================================================
class SupplierResponse(SupplierBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔍 Search params
# =========================================================
class SupplierSearchParams(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    rfc: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")