from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
# Si no tienes esos tipos, puedes usar int directamente

# ============================================
# 🔹 BASE SCHEMA
# ============================================

class SaleBatchUsageBase(BaseModel):
    sale_detail_id: int = Field(..., description="ID del detalle de venta asociado")
    batch_id: int = Field(..., description="ID del lote de producto usado")
    quantity_used: int = Field(..., gt=0, description="Cantidad descontada del lote")


# ============================================
# 🔹 CREATION SCHEMA
# ============================================

class SaleBatchUsageCreate(SaleBatchUsageBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "sale_detail_id": 12,
                "batch_id": 45,
                "quantity_used": 3
            }
        }
    )


# ============================================
# 🔹 UPDATE SCHEMA
# ============================================

class SaleBatchUsageUpdate(BaseModel):
    quantity_used: Optional[int] = Field(None, gt=0, description="Actualizar cantidad usada")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "quantity_used": 5
            }
        }
    )


# ============================================
# 🔹 RESPONSE SCHEMA (BÁSICO)
# ============================================

class SaleBatchUsageResponse(SaleBatchUsageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1001,
                "sale_detail_id": 12,
                "batch_id": 45,
                "quantity_used": 3,
                "created_at": "2025-11-10T14:30:00",
                "updated_at": "2025-11-10T14:35:00"
            }
        }
    )


# ============================================
# 🔹 DETAILED RESPONSE (CON RELACIONES)
# ============================================

class SaleBatchUsageDetailsResponse(SaleBatchUsageResponse):
    # relaciones opcionales (si quieres incluir información del lote o detalle)


    batch: Optional["ProductBatchResponse"] = Field(None, description="Datos del lote asociado")
    sale_detail: Optional["SaleDetailResponse"] = Field(None, description="Detalle de venta asociado")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1001,
                "sale_detail_id": 12,
                "batch_id": 45,
                "quantity_used": 3,
                "created_at": "2025-11-10T14:30:00",
                "updated_at": "2025-11-10T14:35:00",
                "batch": {
                    "id": 45,
                    "lot_code": "L2301",
                    "expiration_date": "2025-07-01",
                    "quantity": 97
                },
                "sale_detail": {
                    "id": 12,
                    "product_id": 5,
                    "price_unit": 20.0,
                    "quantity": 3
                }
            }
        }
    )

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..product_batch.schemas import ProductBatchResponse
    from ..sale_details.schemas import SaleDetailResponse