from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams
from pharmatrack.types.common import FutureOrPresentDate

__all__ = ["PaginatedResponse", "PaginationParams"]


# =========================================================
# 🔹 Base
# =========================================================
class PurchaseBase(BaseModel):
    supplier_id: int = Field(..., ge=1, description="ID del proveedor")
    user_id: int = Field(..., ge=1, description="ID del usuario que registra la compra")
    total: float = Field(..., gt=0, description="Total de la compra")
    description: Optional[str] = Field(None, max_length=2000, description="Notas u observaciones")


# =========================================================
# 🔸 Renglón (lo que llegó); se suma al stock al guardar
# =========================================================
class PurchaseItem(BaseModel):
    product_id: int = Field(..., ge=1, description="ID del producto")
    quantity: float = Field(..., gt=0, description="Cantidad recibida")
    unit_price: float = Field(..., ge=0, description="Precio unitario de compra")
    expiration_date: Optional[FutureOrPresentDate] = Field(None, description="Fecha de vencimiento del lote")
    lot_code: Optional[str] = Field(None, max_length=100, description="Código de lote")

    model_config = ConfigDict(extra="forbid")


class PurchaseItemEdit(PurchaseItem):
    # al editar, un lote ya registrado puede haber vencido
    expiration_date: Optional[date] = None


# =========================================================
# 🟢 Create
# =========================================================
class PurchaseCreate(PurchaseBase):
    date_emision: Optional[datetime] = None
    items: list[PurchaseItem] = Field(default_factory=list)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "supplier_id": 1,
                "user_id": 2,
                "total": 1500.00,
                "description": "Reabastecimiento mensual de medicamentos",
            }
        },
    )


# =========================================================
# 🟡 Update
# =========================================================
class PurchaseUpdate(BaseModel):
    supplier_id: Optional[int] = Field(None, ge=1)
    user_id: Optional[int] = Field(None, ge=1)
    total: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=2000)
    date_emision: Optional[datetime] = None
    # si viene, reemplaza los renglones: resta del stock los viejos y suma los nuevos
    items: Optional[list[PurchaseItemEdit]] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "total": 1800.00,
                "description": "Ajuste por devolución parcial",
            }
        },
    )


# =========================================================
# 🔵 Response
# =========================================================
class PurchaseResponse(PurchaseBase):
    id: int
    date_emision: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


    model_config = ConfigDict(extra="forbid")