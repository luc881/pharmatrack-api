from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# -----------------------
# Base schema
# -----------------------
class PurchaseBase(BaseModel):
    warehouse_id: int = Field(..., description="ID del almacén asociado")
    user_id: int = Field(..., description="ID del usuario que registró la compra")
    branch_id: int = Field(..., description="ID de la sucursal")
    supplier_id: int = Field(..., description="ID del proveedor")

    date_emision: datetime = Field(..., description="Fecha de emisión del comprobante")
    date_entrega: datetime = Field(..., description="Fecha de entrega de la compra")

    state: int = Field(..., ge=1, le=4, description="1=Solicitud, 2=Revisión, 3=Parcial, 4=Entregado")
    type_comprobant: str = Field(..., max_length=100, description="Tipo de comprobante")
    n_comprobant: str = Field(..., max_length=100, description="Número de comprobante")

    total: float = Field(..., description="Monto total de la compra")
    importe: float = Field(..., description="Importe sin impuestos")
    igv: float = Field(..., description="Impuesto IGV aplicado")

    description: Optional[str] = Field(None, description="Descripción o notas adicionales")


# -----------------------
# Create schema
# -----------------------
class PurchaseCreate(PurchaseBase):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "warehouse_id": 1,
                "user_id": 2,
                "branch_id": 3,
                "supplier_id": 5,
                "date_emision": "2024-08-15T12:00:00",
                "date_entrega": "2024-08-20T12:00:00",
                "state": 1,
                "type_comprobant": "Factura",
                "n_comprobant": "FAC-2024-00045",
                "total": 1180.00,
                "importe": 1000.00,
                "igv": 180.00,
                "description": "Compra de insumos electrónicos"
            }
        }
    }


# -----------------------
# Update schema
# -----------------------
class PurchaseUpdate(BaseModel):
    warehouse_id: Optional[int] = None
    user_id: Optional[int] = None
    branch_id: Optional[int] = None
    supplier_id: Optional[int] = None

    date_emision: Optional[datetime] = None
    date_entrega: Optional[datetime] = None
    state: Optional[int] = Field(None, ge=1, le=4)
    type_comprobant: Optional[str] = Field(None, max_length=100)
    n_comprobant: Optional[str] = Field(None, max_length=100)

    total: Optional[float] = None
    importe: Optional[float] = None
    igv: Optional[float] = None

    description: Optional[str] = None
    deleted_at: Optional[datetime] = None

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "state": 2,
                "description": "Compra en revisión antes de aprobación"
            }
        }
    }


# -----------------------
# Response schema
# -----------------------
class PurchaseResponse(PurchaseBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 101,
                "warehouse_id": 1,
                "user_id": 2,
                "branch_id": 3,
                "supplier_id": 5,
                "date_emision": "2024-08-15T12:00:00",
                "date_entrega": "2024-08-20T12:00:00",
                "state": 1,
                "type_comprobant": "Factura",
                "n_comprobant": "FAC-2024-00045",
                "total": 1180.00,
                "importe": 1000.00,
                "igv": 180.00,
                "description": "Compra de insumos electrónicos",
                "created_at": "2024-08-15T12:30:00",
                "updated_at": "2024-08-15T12:30:00",
                "deleted_at": None
            }
        }
    }


# -----------------------
# With relations
# -----------------------
class PurchaseWithRelations(PurchaseResponse):
    # To expand later:
    # supplier: Optional["SupplierResponse"]
    # branch: Optional["BranchResponse"]
    # warehouse: Optional["WarehouseResponse"]
    # user: Optional["UserResponse"]
    pass


# -----------------------
# Search params
# -----------------------
class PurchaseSearchParams(BaseModel):
    state: Optional[int] = None
    supplier_id: Optional[int] = None
    branch_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    user_id: Optional[int] = None
    date_emision_from: Optional[datetime] = None
    date_emision_to: Optional[datetime] = None
    n_comprobant: Optional[str] = None
