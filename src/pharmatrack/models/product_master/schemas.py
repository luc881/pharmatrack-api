from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from pharmatrack.utils.slugify import slugify
from pharmatrack.utils.normalize import norm_title
from ..products.schemas import ProductSimpleResponse, PaginatedResponse, PaginationParams


# =========================================================
# 🔹 Base schema
# =========================================================
class ProductMasterBase(BaseModel):
    name: str = Field(..., max_length=250)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return norm_title(v)


# =========================================================
# 🟢 Create
# =========================================================
class ProductMasterCreate(ProductMasterBase):
    slug: Optional[str] = Field(None, exclude=True)

    @model_validator(mode="after")
    def generate_slug(self) -> "ProductMasterCreate":
        self.slug = slugify(self.name)
        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Paracetamol",
                "description": "Medicamento analgésico y antipirético."
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class ProductMasterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = Field(None, max_length=2000)
    slug: Optional[str] = Field(None, exclude=True)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v):
        return norm_title(v) if v is not None else v

    @model_validator(mode="after")
    def generate_slug_if_name_changed(self) -> "ProductMasterUpdate":
        if self.name is not None:
            self.slug = slugify(self.name)
        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "description": "Analgésico suave ampliamente utilizado"
            }
        }
    )


# =========================================================
# 🔵 Simple Response
# =========================================================
class ProductMasterResponse(ProductMasterBase):
    id: int
    slug: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Paracetamol",
                "slug": "paracetamol",
                "description": "Medicamento analgésico y antipirético.",
                "created_at": "2024-02-12T10:00:00Z"
            }
        }
    )


# =========================================================
# 🧩 Detailed response
# =========================================================
class ProductMasterDetailsResponse(ProductMasterResponse):
    products: Optional[List[ProductSimpleResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔁 Re-exportar para uso en otros módulos
# =========================================================
__all__ = [
    "ProductMasterBase",
    "ProductMasterCreate",
    "ProductMasterUpdate",
    "ProductMasterResponse",
    "ProductMasterDetailsResponse",
    "PaginatedResponse",
    "PaginationParams",
]