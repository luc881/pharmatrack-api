from datetime import datetime
from typing import List, Optional

from pydantic import Field, BaseModel, ConfigDict

from pharmatrack.types.common import ImageURLStr


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    excerpt: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[ImageURLStr] = None
    body: Optional[str] = Field(
        None,
        description='Texto con convenciones: línea en blanco = párrafo, "## " = subtítulo, "> " = cita, "img: URL | pie" = imagen',
    )
    author_name: Optional[str] = Field(None, max_length=100)
    author_role: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    published: bool = False


class ArticleCreate(ArticleBase):
    model_config = ConfigDict(extra="forbid")


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    excerpt: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[ImageURLStr] = None
    body: Optional[str] = None
    author_name: Optional[str] = Field(None, max_length=100)
    author_role: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    published: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class ArticleResponse(ArticleBase):
    id: int
    published_at: Optional[datetime] = None
    reading_minutes: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
