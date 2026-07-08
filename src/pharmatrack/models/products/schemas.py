from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from ..product_has_ingredients.schemas import ProductIngredientCreate, ProductIngredientAmount
# Re-export: muchos módulos importan la paginación desde aquí
from pharmatrack.utils.pagination import PaginationParams, PaginatedResponse  # noqa: F401

from pharmatrack.types.products import (
    ProductTitleStr,
    ProductImageURL,
    ProductDescriptionStr,
    ProductSKUStr,
    PriceRetail,
    PriceCost,
    WarrantyDays,
    AllowWarrantyFlag,
    ProductUnitName,
    ProductBaseUnitName,
    IsUnitSaleFlag,
)
from pharmatrack.utils.slugify import slugify
from pharmatrack.utils.normalize import norm_title, norm_sku, norm_unit


class BulkDeleteRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1, description="IDs a eliminar")


# =========================================================
# 🔹 Mini response (para Brand/Master)
# =========================================================
class ProductSimpleResponse(BaseModel):
    id: int
    title: ProductTitleStr
    sku: Optional[ProductSKUStr] = None
    price_retail: PriceRetail
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 10,
                "title": "Paracetamol 500mg",
                "sku": "PARA500",
                "price_retail": 25.0,
                "is_active": True
            }
        }
    )


# =========================================================
# 🔹 Helper interno: genera slug de producto
# =========================================================
def _product_slug(title: str, sku: Optional[str]) -> str:
    """
    Combines title + sku (if present) into a single slug.
    "Ibuprofeno 400mg" + "IBU400"  →  "ibuprofeno-400mg-ibu400"
    "Ibuprofeno 400mg" + None      →  "ibuprofeno-400mg"
    """
    parts = [title]
    if sku:
        parts.append(sku)
    return slugify(" ".join(parts))


# =========================================================
# 🔹 Base schema
# =========================================================
class ProductBase(BaseModel):
    title: ProductTitleStr
    image: Optional[ProductImageURL] = None

    price_retail: PriceRetail
    price_cost: PriceCost

    description: Optional[ProductDescriptionStr] = None
    sku: Optional[ProductSKUStr] = None

    allow_warranty: AllowWarrantyFlag = False
    warranty_days: Optional[WarrantyDays] = None

    # Units
    is_unit_sale: IsUnitSaleFlag = False
    unit_name: ProductUnitName = Field(default="pieza")
    base_unit_name: Optional[ProductBaseUnitName] = None
    units_per_base: Optional[float] = None

    # 🔥 REQUIRED CATEGORY
    product_category_id: int = Field(..., ge=1)

    is_active: bool = True
    tracks_batches: bool = Field(default=True, description="Si False, el producto no maneja lotes con caducidad ni código")

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str) -> str:
        return norm_title(v)

    @field_validator("sku", mode="before")
    @classmethod
    def normalize_sku(cls, v):
        return norm_sku(v) if v is not None else v

    @field_validator("unit_name", "base_unit_name", mode="before")
    @classmethod
    def normalize_units(cls, v):
        return norm_unit(v) if v is not None else v


# =========================================================
# 🟢 Create
# =========================================================
class ProductCreate(ProductBase):
    brand_id: Optional[int] = None
    product_master_id: Optional[int] = None
    ingredients: Optional[List[ProductIngredientCreate]] = None

    # Auto-generated, not exposed in API docs
    slug: Optional[str] = Field(None, exclude=True)

    @model_validator(mode="after")
    def generate_slug(self) -> "ProductCreate":
        self.slug = _product_slug(self.title, self.sku)
        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Ibuprofeno 400mg",
                "image": "https://example.com/img.png",
                "price_retail": 45.5,
                "price_cost": 30.0,
                "description": "Caja con 10 tabletas",
                "sku": "IBU400",

                "allow_warranty": False,
                "warranty_days": None,

                "is_unit_sale": False,
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,

                "product_category_id": 3,

                "is_active": True,
                "brand_id": 1,
                "product_master_id": 5,

                "ingredients": [
                    {"ingredient_id": 1, "amount": "400 mg"},
                    {"ingredient_id": 2, "amount": "5 mg"}
                ]
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class ProductUpdate(BaseModel):
    title: Optional[ProductTitleStr] = None
    image: Optional[ProductImageURL] = None

    price_retail: Optional[PriceRetail] = None
    price_cost: Optional[PriceCost] = None

    description: Optional[ProductDescriptionStr] = None
    sku: Optional[ProductSKUStr] = None

    allow_warranty: Optional[AllowWarrantyFlag] = None
    warranty_days: Optional[WarrantyDays] = None

    is_unit_sale: Optional[IsUnitSaleFlag] = None
    unit_name: Optional[ProductUnitName] = None
    base_unit_name: Optional[ProductBaseUnitName] = None
    units_per_base: Optional[float] = None

    product_category_id: Optional[int] = None

    is_active: Optional[bool] = None
    tracks_batches: Optional[bool] = None

    brand_id: Optional[int] = None
    product_master_id: Optional[int] = None
    ingredients: Optional[List[ProductIngredientCreate]] = None

    # Auto-generated when title or sku change, not exposed in API docs
    slug: Optional[str] = Field(None, exclude=True)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, v):
        return norm_title(v) if v is not None else v

    @field_validator("sku", mode="before")
    @classmethod
    def normalize_sku(cls, v):
        return norm_sku(v) if v is not None else v

    @field_validator("unit_name", "base_unit_name", mode="before")
    @classmethod
    def normalize_units(cls, v):
        return norm_unit(v) if v is not None else v

    @model_validator(mode="after")
    def generate_slug_if_changed(self) -> "ProductUpdate":
        # Only regenerate if at least title or sku was explicitly sent
        if self.title is not None or self.sku is not None:
            self.slug = _product_slug(
                self.title or "",   # title might not be sent; handled in endpoint
                self.sku
            )
        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Ibuprofeno 400mg - Nueva presentación",
                "image": "https://example.com/new.png",
                "price_retail": 48.0,
                "price_cost": 31.0,
                "description": "Nueva caja de 12 tabletas",
                "sku": "IBU400",

                "is_unit_sale": False,
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,

                "product_category_id": 4,

                "is_active": True,
                "brand_id": 1,
                "product_master_id": 5,

                "ingredients": [
                    {"ingredient_id": 1, "amount": "400 mg"},
                    {"ingredient_id": 2, "amount": "5 mg"}
                ]
            }
        }
    )


# =========================================================
# 🔵 Response (sin relaciones)
# =========================================================
class ProductResponse(ProductBase):
    id: int
    slug: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    brand_id: Optional[int] = None
    product_master_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 12,
                "title": "Ibuprofeno 400mg",
                "slug": "ibuprofeno-400mg-ibu400",
                "image": "https://example.com/img.png",
                "price_retail": 45.5,
                "price_cost": 30.0,
                "description": "Caja con 10 tabletas",
                "sku": "IBU400",

                "is_unit_sale": False,
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,

                "product_category_id": 3,

                "is_active": True,
                "brand_id": 1,
                "product_master_id": 5,

                "created_at": "2024-02-12T10:00:00",
                "updated_at": "2024-02-15T13:22:00"
            }
        }
    )


# =========================================================
# 🧩 Detallado (con relaciones reales)
# =========================================================
class ProductDetailsResponse(ProductResponse):
    brand: Optional["ProductBrandResponse"] = None
    product_master: Optional["ProductMasterResponse"] = None
    category: Optional["ProductCategoryResponse"] = None
    batches: Optional[List["ProductBatchResponse"]] = None
    ingredients: Optional[List[ProductIngredientAmount]] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔁 Forward references
# =========================================================
from ..product_brand.schemas import ProductBrandResponse
from ..product_master.schemas import ProductMasterResponse
from ..product_categories.schemas import ProductCategoryResponse
from ..product_batch.schemas import ProductBatchResponse
from ..ingredients.schemas import IngredientResponse

ProductDetailsResponse.model_rebuild()