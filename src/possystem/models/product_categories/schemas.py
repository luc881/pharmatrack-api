from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ...types.products_categories import (
    CategoryNameStr,
    CategoryImageURL,
    IsCategoryActiveFlag
)

class ProductCategoryBase(BaseModel):
    name: CategoryNameStr = Field(...)
    image: Optional[CategoryImageURL] = None
    is_active: Optional[IsCategoryActiveFlag] = True
    parent_id: Optional[int] = Field(
        None,
        description="ID de la categoría padre (NULL si es raíz)"
    )

class ProductCategoryCreate(ProductCategoryBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Analgésicos",
                "image": None,
                "is_active": True,
                "parent_id": 1
            }
        }
    )

class ProductCategoryUpdate(BaseModel):
    name: Optional[CategoryNameStr] = None
    image: Optional[CategoryImageURL] = None
    is_active: Optional[IsCategoryActiveFlag] = None
    parent_id: Optional[int] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Analgésicos y antipiréticos",
                "parent_id": 1
            }
        }
    )

class ProductCategoryResponse(ProductCategoryBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "Analgésicos",
                "parent_id": 1,
                "is_active": True,
                "created_at": "2024-07-01T12:00:00",
                "updated_at": "2024-07-02T09:30:00"
            }
        }
    )

class ProductCategoryTreeResponse(ProductCategoryResponse):
    children: List["ProductCategoryTreeResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ProductCategoryDetailsResponse(ProductCategoryResponse):
    products: Optional[List["ProductResponse"]] = None
    children: Optional[List["ProductCategoryTreeResponse"]] = None

    model_config = ConfigDict(from_attributes=True)

class ProductCategorySearchParams(BaseModel):
    name: Optional[str] = Field(None, max_length=250)
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None

    model_config = ConfigDict(extra="forbid")

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..products.schemas import ProductResponse

# Pydantic v2
from ..products.schemas import ProductResponse

ProductCategoryTreeResponse.model_rebuild()
ProductCategoryDetailsResponse.model_rebuild()
