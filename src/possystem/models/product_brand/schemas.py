from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ..products.schemas import ProductSimpleResponse


# =========================================================
# 🔹 Base schema
# =========================================================
class ProductBrandBase(BaseModel):
    name: str = Field(..., max_length=200)
    logo: Optional[str] = Field(None, max_length=255)


# =========================================================
# 🟢 Create
# =========================================================
class ProductBrandCreate(ProductBrandBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Genoma Lab",
                "logo": "https://example.com/logos/genomalab.png"
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class ProductBrandUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    logo: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Genoma Lab - Nueva Imagen",
                "logo": "https://example.com/logos/genomalab_v2.png"
            }
        }
    )


# =========================================================
# 🔵 Response simple
# =========================================================
class ProductBrandResponse(ProductBrandBase):
    id: int
    created_at: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Genoma Lab",
                "logo": "https://example.com/logos/genomalab.png",
                "created_at": "2024-02-12T10:00:00Z"
            }
        }
    )


# =========================================================
# 🧩 Detailed response (con productos)
# =========================================================
class ProductBrandDetailsResponse(ProductBrandResponse):
    products: Optional[List[ProductSimpleResponse]] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Genoma Lab",
                "logo": "https://example.com/logos/genomalab.png",
                "created_at": "2024-02-12T10:00:00Z",

                "products": [
                    {
                        "id": 10,
                        "title": "Paracetamol 500mg",
                        "sku": "PARA500",
                        "price_retail": 25.0,
                        "is_active": True
                    },
                    {
                        "id": 11,
                        "title": "Ibuprofeno 400mg",
                        "sku": "IBU400",
                        "price_retail": 45.5,
                        "is_active": True
                    }
                ]
            }
        }
    )


# =========================================================
# 🔁 Forward references
# =========================================================
if TYPE_CHECKING:
    from ..products.schemas import ProductSimpleResponse
