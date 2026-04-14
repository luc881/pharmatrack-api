from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams

__all__ = ["PaginatedResponse", "PaginationParams"]


# =========================================================
# 🔹 Base
# =========================================================
class PurchaseDetailBase(BaseModel):
    purchase_id: int = Field(..., ge=1, description="ID de la compra")
    product_id: int = Field(..., ge=1, description="ID del producto")
    quantity: float = Field(..., gt=0, description="Cantidad recibida")
    unit_price: float = Field(..., ge=0, description="Precio unitario de compra")
    expiration_date: Optional[date] = Field(None, description="Fecha de vencimiento del lote")
    lot_code: Optional[str] = Field(None, max_length=100, description="Código de lote")


# =========================================================
# 🟢 Create
# =========================================================
class PurchaseDetailCreate(PurchaseDetailBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "purchase_id": 1,
                "product_id": 5,
                "quantity": 100,
                "unit_price": 12.50,
                "expiration_date": "2027-06-30",
                "lot_code": "LOT-2025-001",
            }
        },
    )


# =========================================================
# 🟡 Update
# =========================================================
class PurchaseDetailUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, ge=0)
    expiration_date: Optional[date] = None
    lot_code: Optional[str] = Field(None, max_length=100)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "quantity": 90,
                "unit_price": 11.00,
                "expiration_date": "2027-03-15",
                "lot_code": "LOT-2025-002",
            }
        },
    )


# =========================================================
# 🔵 Response
# =========================================================
class PurchaseDetailResponse(PurchaseDetailBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔍 Search params
# =========================================================
class PurchaseDetailSearchParams(BaseModel):
    purchase_id: Optional[int] = Field(None, ge=1)
    product_id: Optional[int] = Field(None, ge=1)
    lot_code: Optional[str] = None

    model_config = ConfigDict(extra="forbid")