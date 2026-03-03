from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# =========================================================
# 🔹 Base
# =========================================================
class PurchaseBase(BaseModel):
    supplier_id: int = Field(..., ge=1, description="ID del proveedor")
    user_id: int = Field(..., ge=1, description="ID del usuario que registra la compra")
    total: float = Field(..., gt=0, description="Total de la compra")
    description: Optional[str] = Field(None, max_length=2000, description="Notas u observaciones")


# =========================================================
# 🟢 Create
# =========================================================
class PurchaseCreate(PurchaseBase):
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


# =========================================================
# 🔍 Search params
# =========================================================
class PurchaseSearchParams(BaseModel):
    supplier_id: Optional[int] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(extra="forbid")