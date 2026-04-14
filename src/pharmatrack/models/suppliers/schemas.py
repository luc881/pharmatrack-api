from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams

__all__ = ["PaginatedResponse", "PaginationParams"]


# =========================================================
# 🔹 Base
# =========================================================
class SupplierBase(BaseModel):
    name: str = Field(..., max_length=255, description="Nombre o razón social del proveedor")
    logo: Optional[str] = Field(None, max_length=255, description="URL del logo o imagen")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    phone: Optional[str] = Field(None, max_length=25, description="Teléfono de contacto")
    address: Optional[str] = Field(None, max_length=250, description="Dirección")
    rfc: Optional[str] = Field(None, max_length=50, description="RFC / identificación tributaria")
    is_active: bool = Field(True, description="Estado del proveedor")


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
    name: Optional[str] = Field(None, max_length=255)
    logo: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=25)
    address: Optional[str] = Field(None, max_length=250)
    rfc: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

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