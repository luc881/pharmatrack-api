from typing import Optional, TYPE_CHECKING
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..products.schemas import PaginatedResponse, PaginationParams


# =========================================================
# 🔹 Base schema
# =========================================================
class ProductBatchBase(BaseModel):
    lot_code: Optional[str] = Field(None, max_length=100, description="Código o identificador del lote")
    expiration_date: date = Field(..., description="Fecha de caducidad del lote")
    quantity: int = Field(..., ge=0, description="Cantidad disponible en el lote")
    purchase_price: Optional[float] = Field(None, ge=0, description="Precio de compra por unidad del lote")

    model_config = dict(from_attributes=True)

    @field_validator("lot_code", mode="before")
    def normalize_text(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v


# =========================================================
# 🟢 Create
# =========================================================
class ProductBatchCreate(ProductBatchBase):
    product_id: int = Field(..., gt=0, description="ID del producto asociado")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "product_id": 1,
                "lot_code": "A2025-01",
                "expiration_date": "2025-12-15",
                "quantity": 100,
                "purchase_price": 12.50
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class ProductBatchUpdate(BaseModel):
    lot_code: Optional[str] = Field(None, max_length=100)
    expiration_date: Optional[date] = None
    quantity: Optional[int] = Field(None, ge=0)
    purchase_price: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "quantity": 80,
                "expiration_date": "2025-11-30"
            }
        }
    )


# =========================================================
# 🔵 Response (sin relaciones)
# =========================================================
class ProductBatchResponse(ProductBatchBase):
    id: int
    product_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 10,
                "product_id": 1,
                "lot_code": "A2025-01",
                "expiration_date": "2025-12-15",
                "quantity": 100,
                "purchase_price": 12.50,
                "created_at": "2025-06-01T14:25:00"
            }
        }
    )


# =========================================================
# 🧩 Detailed response (con relación al producto)
# =========================================================
class ProductBatchDetailsResponse(ProductBatchResponse):
    product: Optional["ProductResponse"] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 10,
                "lot_code": "A2025-01",
                "expiration_date": "2025-12-15",
                "quantity": 100,
                "purchase_price": 12.50,
                "product": {
                    "id": 1,
                    "title": "Paracetamol 500mg",
                    "price_retail": 20.0,
                    "price_cost": 18.0,
                    "sku": "PARA500",
                    "is_active": True
                }
            }
        }
    )


# =========================================================
# 🔁 Forward references
# =========================================================
if TYPE_CHECKING:
    from ..products.schemas import ProductResponse

from ..products.schemas import ProductResponse  # noqa: E402
ProductBatchDetailsResponse.model_rebuild()


# =========================================================
# 🔁 Re-exportar para uso en el router
# =========================================================
__all__ = [
    "ProductBatchBase",
    "ProductBatchCreate",
    "ProductBatchUpdate",
    "ProductBatchResponse",
    "ProductBatchDetailsResponse",
    "PaginatedResponse",
    "PaginationParams",
]