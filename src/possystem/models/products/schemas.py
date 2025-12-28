from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ..product_has_ingredients.schemas import ProductIngredientCreate, ProductIngredientAmount

from possystem.types.products import (
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
    IsActiveFlag,
)

# =========================================================
# 🔹 Mini response (para Brand/Master)
# =========================================================
class ProductSimpleResponse(BaseModel):
    id: int
    title: ProductTitleStr
    sku: Optional[ProductSKUStr] = None
    price_retail: PriceRetail
    is_active: IsActiveFlag

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

    # 🔹 NUEVO
    is_unit_sale: IsUnitSaleFlag = False
    unit_name: ProductUnitName = Field(default="pieza")
    base_unit_name: Optional[ProductBaseUnitName] = None
    units_per_base: Optional[float] = None

    is_active: IsActiveFlag = True


# =========================================================
# 🟢 Create
# =========================================================
class ProductCreate(ProductBase):
    brand_id: Optional[int] = Field(None)
    product_master_id: Optional[int] = Field(None)
    ingredients: Optional[List[ProductIngredientCreate]] = None

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
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,
                "is_active": True,
                "is_unit_sale": False,
                "brand_id": 1,
                "product_master_id": None,
                "ingredients": [
                    {"ingredient_id": 1, "amount": "500 mg"},
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

    # 🔹 NUEVO
    is_unit_sale: Optional[IsUnitSaleFlag] = None
    unit_name: Optional[ProductUnitName] = None
    base_unit_name: Optional[ProductBaseUnitName] = None
    units_per_base: Optional[float] = None

    is_active: Optional[IsActiveFlag] = None

    brand_id: Optional[int] = None
    product_master_id: Optional[int] = None
    ingredients: Optional[List[ProductIngredientCreate]] = None

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
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,
                "is_unit_sale": False,
                "is_active": True,
                "ingredients": [
                    {"ingredient_id": 1, "amount": "500 mg"},
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    brand_id: Optional[int] = None
    product_master_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 12,
                "title": "Ibuprofeno 400mg",
                "image": "https://example.com/img.png",
                "price_retail": 45.5,
                "price_cost": 30.0,
                "description": "Caja con 10 tabletas",
                "sku": "IBU400",
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,
                "is_unit_sale": False,
                "is_active": True,
                "brand_id": 1,
                "product_master_id": None,
                "created_at": "2024-02-12T10:00:00Z",
                "updated_at": "2024-02-15T13:22:00Z"
            }
        }
    )


# =========================================================
# 🧩 Detallado (con relaciones reales)
# =========================================================
class ProductDetailsResponse(ProductResponse):
    brand: Optional["ProductBrandResponse"] = None
    product_master: Optional["ProductMasterResponse"] = None
    batches: Optional[List["ProductBatchResponse"]] = None

    ingredients: Optional[List[ProductIngredientAmount]] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 12,
                "title": "Ibuprofeno 400mg",
                "image": "https://example.com/img.png",
                "price_retail": 45.5,
                "price_cost": 30.0,
                "description": "Caja con 10 tabletas",
                "sku": "IBU400",
                "unit_name": "pieza",
                "base_unit_name": None,
                "units_per_base": None,
                "is_unit_sale": False,
                "is_active": True,
                "brand_id": 1,
                "product_master_id": 5,
                "created_at": "2024-02-12T10:00:00Z",
                "updated_at": "2024-02-15T13:22:00Z",

                "brand": {"id": 1, "name": "Genfar"},

                "product_master": {
                    "id": 5,
                    "name": "Analgésicos",
                    "description": "Medicamentos para dolor"
                },

                "batches": [
                    {
                        "id": 101,
                        "batch_number": "L202401A",
                        "expiration_date": "2026-01-01",
                        "quantity": 35
                    }
                ],

                "ingredients": [
                    {
                        "ingredient_id": 1,
                        "amount": "500 mg",
                        "ingredient": {"id": 1, "name": "Ibuprofeno"}
                    }
                ]
            }
        }
    )


# =========================================================
# 🔍 Search params
# =========================================================
class ProductSearchParams(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Texto parcial para buscar en el título (ILIKE)"
    )

    # 🔹 NUEVO
    is_unit_sale: Optional[bool] = Field(
        None,
        description="Filtrar productos de venta suelta o presentación"
    )

    is_active: Optional[bool] = Field(
        None,
        description="Filtrar productos activos/inactivos"
    )

    brand_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID de la marca"
    )

    product_master_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID del master"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "ibu",
                "is_active": True,
                "brand_id": 1,
                "product_master_id": 5
            }
        }
    )


# =========================================================
# 🔁 Forward references
# =========================================================
if TYPE_CHECKING:
    from ..product_batch.schemas import ProductBatchResponse
    from ..product_brands.schemas import ProductBrandResponse
    from ..product_master.schemas import ProductMasterResponse
    from ..ingredients.schemas import IngredientResponse
