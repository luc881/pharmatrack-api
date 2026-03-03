from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, TYPE_CHECKING


# ============================================
# 🔹 BASE
# ============================================
class SaleBatchUsageBase(BaseModel):
    sale_detail_id: int = Field(
        ..., gt=0, description="ID del detalle de venta asociado"
    )
    batch_id: int = Field(
        ..., gt=0, description="ID del lote de producto usado"
    )
    quantity_used: int = Field(
        ..., gt=0, description="Cantidad descontada del lote"
    )


# ============================================
# 🟢 CREATE  (uso interno — complete_sale)
# ============================================
class SaleBatchUsageCreate(SaleBatchUsageBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "sale_detail_id": 12,
                "batch_id": 45,
                "quantity_used": 3,
            }
        },
    )


# ============================================
# 🟡 UPDATE  (auditoría / corrección puntual)
# ============================================
class SaleBatchUsageUpdate(BaseModel):
    quantity_used: Optional[int] = Field(
        None, gt=0, description="Nueva cantidad usada del lote"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"quantity_used": 5}},
    )


# ============================================
# 🔵 RESPONSE
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
                "updated_at": "2025-11-10T14:35:00",
            }
        },
    )


# ============================================
# 🧩 RESPONSE CON RELACIONES
# ============================================
class SaleBatchUsageDetailsResponse(SaleBatchUsageResponse):
    batch: Optional["ProductBatchResponse"] = Field(
        None, description="Información del lote utilizado"
    )
    sale_detail: Optional["SaleDetailResponse"] = Field(
        None, description="Detalle de venta asociado"
    )

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
                    "quantity": 97,
                },
                "sale_detail": {
                    "id": 12,
                    "product_id": 5,
                    "price_unit": 20.0,
                    "quantity": 3,
                },
            }
        },
    )


# ============================================
# 🔁 Forward references
# ============================================
if TYPE_CHECKING:
    from ..product_batch.schemas import ProductBatchResponse
    from ..sale_details.schemas import SaleDetailResponse

# Necesario para que Pydantic resuelva los tipos al importar el módulo
from ..product_batch.schemas import ProductBatchResponse  # noqa: E402
from ..sale_details.schemas import SaleDetailResponse  # noqa: E402

SaleBatchUsageDetailsResponse.model_rebuild()