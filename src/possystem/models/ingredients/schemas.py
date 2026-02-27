from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
import re

from possystem.types.ingredients import (
    IngredientTitleStr,
    IngredientDescriptionStr,
)
from possystem.models.products.schemas import PaginatedResponse, PaginationParams
from possystem.utils.slugify import slugify


# =========================================================
# 🔹 Base
# =========================================================
class IngredientBase(BaseModel):
    name: IngredientTitleStr
    description: Optional[IngredientDescriptionStr] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"^[a-z0-9._\- ]+$", v):
            raise ValueError("Invalid ingredient name")
        return v


# =========================================================
# 🟢 Create
# =========================================================
class IngredientCreate(IngredientBase):
    # slug is auto-generated from name, not exposed to the user
    slug: Optional[str] = Field(None, exclude=True)

    @model_validator(mode="after")
    def generate_slug(self) -> "IngredientCreate":
        self.slug = slugify(self.name)
        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "paracetamol",
                "description": "Analgesic and antipyretic"
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, exclude=True)

    @field_validator("name")
    @classmethod
    def normalize_optional(cls, v):
        if v is None:
            return v
        v = v.strip().lower()
        if not re.fullmatch(r"^[a-z0-9._\- ]+$", v):
            raise ValueError("Invalid ingredient name")
        return v

    @model_validator(mode="after")
    def generate_slug_if_name_changed(self) -> "IngredientUpdate":
        if self.name is not None:
            self.slug = slugify(self.name)
        return self

    model_config = ConfigDict(extra="forbid")


# =========================================================
# 🔵 Response
# =========================================================
class IngredientResponse(IngredientBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔁 Re-exportar para uso en el router
# =========================================================
__all__ = [
    "IngredientBase",
    "IngredientCreate",
    "IngredientUpdate",
    "IngredientResponse",
    "PaginatedResponse",
    "PaginationParams",
]