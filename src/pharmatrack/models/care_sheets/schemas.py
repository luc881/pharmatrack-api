from datetime import datetime
from typing import List, Optional

from pydantic import Field, BaseModel, ConfigDict

from pharmatrack.types.common import ImageURLStr

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class TaxonRow(BaseModel):
    rank: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=200)
    italic: bool = False


class Fact(BaseModel):
    label: str = Field(..., min_length=1, max_length=60)
    value: str = Field(..., min_length=1, max_length=120)


class MorphologyItem(BaseModel):
    label: str = Field(..., min_length=1, max_length=60)
    text: str = Field(..., min_length=1, max_length=1000)


class Photo(BaseModel):
    src: ImageURLStr
    alt: str = Field(..., min_length=1, max_length=200)


class Video(BaseModel):
    src: str = Field(..., pattern=r"^https://", max_length=500)
    alt: str = Field(..., min_length=1, max_length=200)


class Reference(BaseModel):
    text: str = Field(..., min_length=1, max_length=600)
    url: Optional[str] = Field(None, pattern=r"^https?://", max_length=500)


class CareSheetContent(BaseModel):
    authority: Optional[str] = Field(None, max_length=200)
    origin: Optional[str] = Field(None, max_length=150)
    difficulty: Optional[str] = Field(None, max_length=50)
    summary: str = Field(..., min_length=1, max_length=600)
    taxonomy: List[TaxonRow] = Field(default_factory=list)
    facts: List[Fact] = Field(default_factory=list)
    basics: List[str] = Field(default_factory=list)
    body: Optional[str] = Field(None, description='Markdown; cada "## " es una sección')
    morphology: List[MorphologyItem] = Field(default_factory=list)
    habitat: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list, max_length=12)
    photos: List[Photo] = Field(default_factory=list)
    video: Optional[Video] = None
    references: List[Reference] = Field(default_factory=list)


class CareSheetCreate(CareSheetContent):
    species_id: int = Field(..., gt=0)
    # vacío = se arma del nombre de la especie ("phyllium-gardabagusi-argopuro")
    slug: Optional[str] = Field(None, pattern=SLUG, max_length=150)
    published: bool = False

    model_config = ConfigDict(extra="forbid")


class CareSheetUpdate(CareSheetContent):
    """Reemplazo completo (el editor manda la ficha entera)."""
    species_id: int = Field(..., gt=0)
    slug: str = Field(..., pattern=SLUG, max_length=150)
    published: bool = False

    model_config = ConfigDict(extra="forbid")


class CareSheetGroup(BaseModel):
    id: int
    name: str


class CareSheetSummary(BaseModel):
    """Renglón del índice /fichas (sin cuerpo)."""
    id: int
    slug: str
    species_id: int
    scientific_name: str
    locality: Optional[str] = None
    common_name: Optional[str] = None
    group: Optional[CareSheetGroup] = None
    difficulty: Optional[str] = None
    summary: str
    cover: Optional[str] = None
    published: bool = False
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # ejemplares disponibles de la especie (solo en el público)
    available_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CareSheetResponse(CareSheetContent):
    id: int
    slug: str
    species_id: int
    scientific_name: str
    locality: Optional[str] = None
    common_name: Optional[str] = None
    group: Optional[CareSheetGroup] = None
    published: bool = False
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
