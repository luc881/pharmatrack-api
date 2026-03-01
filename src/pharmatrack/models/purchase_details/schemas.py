from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# -----------------------
# Base schema
# -----------------------
class PurchaseDetailBase(BaseModel):
    purchase_id: int = Field(..., description="ID de la compra asociada")
    product_id: int = Field(..., description="ID del producto")
    unit_id: int = Field(..., description="ID de la unidad de medida")

    quantity: float = Field(..., gt=0, description="Cantidad solicitada")
    unit_price: float = Field(..., ge=0, description="Precio unitario")
    total_price: float = Field(..., ge=0, description="Precio total calculado")

    status: int = Field(..., ge=1, le=2, description="1=REQUESTED, 2=DELIVERED")
    description: Optional[str] = Field(None, description="Notas o detalles adicionales")


# -----------------------
# Create schema
# -----------------------
class PurchaseDetailCreate(PurchaseDetailBase):
    delivered_by_id: Optional[int] = Field(None, description="Usuario que entregó el producto")
    delivered_at: Optional[datetime] = Field(None, description="Fecha de entrega del producto")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "purchase_id": 101,
                "product_id": 20,
                "unit_id": 3,
                "quantity": 50,
                "unit_price": 25.5,
                "total_price": 1275.0,
                "status": 1,
                "delivered_by_id": None,
                "delivered_at": None,
                "description": "Compra de resistencias de 10kΩ"
            }
        }
    }


# -----------------------
# Update schema
# -----------------------
class PurchaseDetailUpdate(BaseModel):
    purchase_id: Optional[int] = None
    product_id: Optional[int] = None
    unit_id: Optional[int] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, ge=0)
    total_price: Optional[float] = Field(None, ge=0)
    status: Optional[int] = Field(None, ge=1, le=2)
    delivered_by_id: Optional[int] = None
    delivered_at: Optional[datetime] = None
    description: Optional[str] = None
    deleted_at: Optional[datetime] = None

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "status": 2,
                "delivered_by_id": 7,
                "delivered_at": "2024-08-21T15:00:00",
                "description": "Entregado por almacén central"
            }
        }
    }


# -----------------------
# Response schema
# -----------------------
class PurchaseDetailResponse(PurchaseDetailBase):
    id: int
    delivered_by_id: Optional[int]
    delivered_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 5001,
                "purchase_id": 101,
                "product_id": 20,
                "unit_id": 3,
                "quantity": 50,
                "unit_price": 25.5,
                "total_price": 1275.0,
                "status": 2,
                "delivered_by_id": 7,
                "delivered_at": "2024-08-21T15:00:00",
                "description": "Entregado por almacén central",
                "created_at": "2024-08-15T12:30:00",
                "updated_at": "2024-08-21T15:00:00",
                "deleted_at": None
            }
        }
    }


# -----------------------
# With relations
# -----------------------
class PurchaseDetailWithRelations(PurchaseDetailResponse):
    # To expand later:
    # product: Optional["ProductResponse"]
    # unit: Optional["UnitResponse"]
    # purchase: Optional["PurchaseResponse"]
    pass


# -----------------------
# Search params
# -----------------------
class PurchaseDetailSearchParams(BaseModel):
    purchase_id: Optional[int] = None
    product_id: Optional[int] = None
    unit_id: Optional[int] = None
    status: Optional[int] = None
    delivered_by_id: Optional[int] = None
    delivered_at_from: Optional[datetime] = None
    delivered_at_to: Optional[datetime] = None
