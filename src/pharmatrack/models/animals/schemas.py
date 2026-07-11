from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator

from pharmatrack.types.animals import AnimalSexEnum, AnimalStatusEnum
from pharmatrack.types.common import DescriptionStr, ImageURLStr
from pharmatrack.utils.normalize import norm_title


# =========================================================
# 🔹 Genus
# =========================================================
class GenusBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return norm_title(v)


class GenusCreate(GenusBase):
    model_config = ConfigDict(extra="forbid")


class GenusUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v):
        return norm_title(v) if v is not None else v

    model_config = ConfigDict(extra="forbid")


class GenusResponse(GenusBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔹 Species
# =========================================================
class SpeciesBase(BaseModel):
    genus_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    common_name: Optional[str] = Field(None, min_length=1, max_length=150)

    @field_validator("name", "common_name", mode="before")
    @classmethod
    def normalize_names(cls, v):
        return norm_title(v) if v is not None else v


class SpeciesCreate(SpeciesBase):
    model_config = ConfigDict(extra="forbid")


class SpeciesUpdate(BaseModel):
    genus_id: Optional[int] = Field(None, ge=1)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    common_name: Optional[str] = Field(None, min_length=1, max_length=150)

    @field_validator("name", "common_name", mode="before")
    @classmethod
    def normalize_names(cls, v):
        return norm_title(v) if v is not None else v

    model_config = ConfigDict(extra="forbid")


class SpeciesResponse(SpeciesBase):
    id: int
    genus: Optional[GenusResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔹 Morph
# =========================================================
class MorphBase(BaseModel):
    species_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[DescriptionStr] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return norm_title(v)


class MorphCreate(MorphBase):
    model_config = ConfigDict(extra="forbid")


class MorphUpdate(BaseModel):
    species_id: Optional[int] = Field(None, ge=1)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[DescriptionStr] = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v):
        return norm_title(v) if v is not None else v

    model_config = ConfigDict(extra="forbid")


class MorphResponse(MorphBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔹 Animal
# =========================================================
class AnimalBase(BaseModel):
    species_id: int = Field(..., ge=1)
    sex: AnimalSexEnum = AnimalSexEnum.UNKNOWN
    birth_date: Optional[date] = None
    price: float = Field(..., ge=0)
    price_cost: float = Field(0, ge=0)
    description: Optional[DescriptionStr] = None
    image: Optional[ImageURLStr] = None


class AnimalCreate(AnimalBase):
    code: Optional[str] = Field(
        None, min_length=1, max_length=50,
        description="Identificador único del animal; se genera automáticamente si se omite",
    )
    morph_ids: List[int] = Field(default_factory=list)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "species_id": 1,
                "sex": "female",
                "birth_date": "2025-09-15",
                "price": 3500.0,
                "price_cost": 1200.0,
                "code": "BP-2025-001",
                "morph_ids": [1, 2],
                "description": "Ball python hembra Banana Pastel",
            }
        },
    )


class AnimalUpdate(BaseModel):
    species_id: Optional[int] = Field(None, ge=1)
    sex: Optional[AnimalSexEnum] = None
    birth_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    price_cost: Optional[float] = Field(None, ge=0)
    description: Optional[DescriptionStr] = None
    image: Optional[ImageURLStr] = None
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    morph_ids: Optional[List[int]] = None
    status: Optional[AnimalStatusEnum] = None

    @field_validator("status")
    @classmethod
    def forbid_manual_sold(cls, v):
        # "sold" lo asigna el flujo de venta, nunca el cliente
        if v == AnimalStatusEnum.SOLD:
            raise ValueError("status 'sold' is managed by the sale flow and cannot be set manually")
        return v

    model_config = ConfigDict(extra="forbid")


class AnimalResponse(AnimalBase):
    id: int
    code: str
    status: AnimalStatusEnum
    product_id: int
    species: Optional[SpeciesResponse] = None
    morphs: List[MorphResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
