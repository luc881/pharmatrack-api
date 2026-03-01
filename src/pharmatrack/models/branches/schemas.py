from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
import re



# ---------------------------
# Base (campos compartidos)
# ---------------------------
class BranchBase(BaseModel):
    name: str = Field(..., max_length=255, description="Nombre de la sucursal")
    address: str = Field(..., max_length=255, description="Dirección física de la sucursal")

    @model_validator(mode='before')
    @classmethod
    def strip_all_strings(cls, values):
        # Asegurarse de que siempre sea un diccionario
        if not isinstance(values, dict):
            values = vars(values)

        clean = {}
        for key, value in values.items():
            if isinstance(value, str):
                clean[key] = value.strip().lower()
            else:
                clean[key] = value
        return clean

    model_config = ConfigDict(
        from_attributes= True,
        json_schema_extra = {
            "example": {
                "name": "Sucursal Centro",
                "address": "Av. Principal 123, CDMX",
            }
        }
)


# ---------------------------
# Create
# ---------------------------
class BranchCreate(BranchBase):
    # Si en el futuro agregas más campos que sean solo para creación, hazlo aquí.
    model_config = ConfigDict(
        extra= "forbid",
        json_schema_extra= {
            "example": {
                "name": "Sucursal Norte",
                "address": "Calle 5 #234, Monterrey",
            }
        }
    )


# ---------------------------
# Update (todos opcionales)
# ---------------------------
class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Nuevo nombre de la sucursal")
    address: Optional[str] = Field(None, max_length=255, description="Nueva dirección")

    model_config = ConfigDict(
        extra= "forbid",
        json_schema_extra= {
            "example": {
                "name": "Sucursal Norte Renovada",
                "address": "Calle 5 #234, Monterrey2",
            }
        }
    )


# ---------------------------
# Response (lectura estándar)
# ---------------------------
class BranchResponse(BranchBase):
    id: int
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    model_config = ConfigDict(
        from_attributes= True,  # Permite usar .from_orm / en Pydantic v2: from_attributes
        json_schema_extra= {
            "example": {
                "id": 10,
                "name": "Sucursal Centro",
                "address": "Av. Principal 123, CDMX",
                "created_at": "2024-07-01T10:15:00",
                "updated_at": "2024-07-05T09:00:00",
            }
        }
    )


class BranchWithUsersResponse(BranchResponse):
    users: list["UserResponse"] = Field(default_factory=list, description="Lista de usuarios asociados a la sucursal")

    model_config = ConfigDict(
        from_attributes= True,  # Permite usar .from_orm / en Pydantic v2: from_attributes
        json_schema_extra= {
            "example": {
                "id": 10,
                "name": "Sucursal Centro",
                "address": "Av. Principal 123, CDMX",
                "created_at": "2024-07-01T10:15:00",
                "updated_at": "2024-07-05T09:00:00",
                "users": [
                    {
                        "id": 1,
                        "name": "Juan",
                        "surname": "Pérez",
                        "email": "juan.perez@example.com",
                        "email_verified_at": "2024-06-01T12:34:56",
                        "avatar": "http://example.com/avatar.jpg",
                        "phone": "5551234567",
                        "type_document": "INE",
                        "n_document": "ABC123456",
                        "gender": "M",
                        "created_at": "2024-06-01T12:00:00",
                        "updated_at": "2024-06-02T10:00:00",
                    }
                ]
            }
        }
    )

# ---------------------------
# (Opcional) Respuesta extendida con métricas ligeras
# Útil para listados si quieres devolver conteos relacionados sin anidar objetos pesados
# ---------------------------
class BranchStatsResponse(BranchResponse):
    users_count: Optional[int] = Field(None, description="Número de usuarios asociados")
    warehouses_count: Optional[int] = Field(None, description="Número de almacenes")
    product_wallets_count: Optional[int] = Field(None, description="Número de wallets de productos")
    clients_count: Optional[int] = Field(None, description="Número de clientes")
    sales_count: Optional[int] = Field(None, description="Número de ventas")
    purchases_count: Optional[int] = Field(None, description="Número de compras")

    model_config = ConfigDict(
        from_attributes= True,
        json_schema_extra= {
            "example": {
                "id": 10,
                "name": "Sucursal Centro",
                "address": "Av. Principal 123, CDMX",
                "created_at": "2024-07-01T10:15:00",
                "updated_at": "2024-07-05T09:00:00",
                "users_count": 12,
                "warehouses_count": 3,
                "product_wallets_count": 45,
                "clients_count": 230,
                "sales_count": 1290,
                "purchases_count": 87
            }
        }
    )


# ---------------------------
# (Opcional) Lista paginada
# ---------------------------
class BranchListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[BranchResponse]

    model_config = ConfigDict(
        json_schema_extra= {
            "example": {
                "total": 25,
                "page": 1,
                "size": 10,
                "items": [
                    {
                        "id": 1,
                        "name": "Sucursal Centro",
                        "address": "Av. Principal 123, CDMX",
                        "created_at": "2024-07-01T10:15:00",
                        "updated_at": "2024-07-05T09:00:00",
                    }
                ]
            }
        }
    )

# Forward reference resolution
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users.schemas import UserResponse