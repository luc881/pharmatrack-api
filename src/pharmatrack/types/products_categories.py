# app/schemas/types_product_category.py
from typing import Annotated, Optional
from pydantic import StringConstraints, Field, HttpUrl
from enum import Enum
from pharmatrack.types.common import ImageURLStr, IsActiveFlag

# Aliases semánticos desde common
CategoryImageURL = ImageURLStr
IsCategoryActiveFlag = IsActiveFlag


# -------------------------------
# 🔤 String types
# -------------------------------

CategoryNameStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=250,
        pattern=r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\-.,'\"() ]+$"
    ),
    Field(description="Nombre de la categoría de producto")
]

# CategoryImageURL e IsCategoryActiveFlag importados desde common.py (ver arriba)


# -------------------------------
# 🧭 Enumerations (si deseas agregar estados en el futuro)
# -------------------------------

class CategoryStateEnum(int, Enum):
    ACTIVE = 1       # Activa
    INACTIVE = 2     # Inactiva
    ARCHIVED = 3     # Archivada (opcional, para uso futuro)


# -------------------------------
# 🧩 Extras o identificadores
# -------------------------------

CategoryID = Annotated[
    int,
    Field(ge=1, description="Identificador único de la categoría")
]

