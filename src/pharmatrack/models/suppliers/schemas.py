from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# -----------------------
# Base schema
# -----------------------
class SupplierBase(BaseModel):
    full_name: str = Field(..., max_length=255, description="Nombre completo del proveedor")
    state: int = Field(..., ge=1, le=2, description="1=Activo, 2=Inactivo")

    imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen o logo")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    phone: Optional[str] = Field(None, max_length=25, description="Teléfono")
    address: Optional[str] = Field(None, max_length=250, description="Dirección")
    ruc: Optional[str] = Field(None, max_length=50, description="RUC - Identificación tributaria")


# -----------------------
# Create schema
# -----------------------
class SupplierCreate(SupplierBase):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "full_name": "Distribuidora ABC S.A.",
                "imagen": "https://example.com/logo.png",
                "email": "contacto@abc.com",
                "phone": "+52 555-123-4567",
                "address": "Av. Reforma 123, CDMX",
                "state": 1,
                "ruc": "ABC123456789"
            }
        }
    }


# -----------------------
# Update schema
# -----------------------
class SupplierUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    imagen: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=25)
    address: Optional[str] = Field(None, max_length=250)
    state: Optional[int] = Field(None, ge=1, le=2)
    ruc: Optional[str] = Field(None, max_length=50)
    deleted_at: Optional[datetime] = None

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "full_name": "Distribuidora ABC S.A. de C.V.",
                "phone": "+52 555-987-6543",
                "state": 2
            }
        }
    }


# -----------------------
# Response schema
# -----------------------
class SupplierResponse(SupplierBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 10,
                "full_name": "Distribuidora ABC S.A.",
                "imagen": "https://example.com/logo.png",
                "email": "contacto@abc.com",
                "phone": "+52 555-123-4567",
                "address": "Av. Reforma 123, CDMX",
                "state": 1,
                "ruc": "ABC123456789",
                "created_at": "2024-08-01T12:00:00",
                "updated_at": "2024-08-05T15:30:00",
                "deleted_at": None
            }
        }
    }


# -----------------------
# With relations
# -----------------------
class SupplierWithRelations(SupplierResponse):
    # Placeholder for when you link products, purchases, etc.
    # Example: products: list["ProductResponse"] = []
    pass


# -----------------------
# Search params
# -----------------------
class SupplierSearchParams(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[int] = None
    ruc: Optional[str] = None
