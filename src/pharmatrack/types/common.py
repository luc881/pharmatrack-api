"""
Tipos Pydantic reutilizables en toda la API.
Importar desde aquí en lugar de redefinir en cada módulo.
"""
from decimal import Decimal
from typing import Annotated, Optional
from pydantic import StringConstraints, Field, HttpUrl
from pydantic.types import NonNegativeFloat


# -----------------------------------------------
# 💰 Tipos monetarios
# -----------------------------------------------

MoneyAmount = Annotated[
    Decimal,
    Field(ge=Decimal("0"), decimal_places=2, description="Importe monetario (≥ 0, 2 decimales)")
]

NonNegativeMoneyAmount = Annotated[
    Decimal,
    Field(ge=Decimal("0"), decimal_places=2, description="Importe monetario no negativo")
]


# -----------------------------------------------
# 📊 Porcentajes
# -----------------------------------------------

PercentageValue = Annotated[
    Optional[NonNegativeFloat],
    Field(le=100, description="Porcentaje (0–100)")
]

TaxPercentage = Annotated[
    Optional[NonNegativeFloat],
    Field(le=100, description="Porcentaje de impuesto (0–100)")
]

DiscountPercentage = Annotated[
    Optional[NonNegativeFloat],
    Field(le=100, description="Porcentaje de descuento máximo permitido (0–100)")
]


# -----------------------------------------------
# 🔤 Strings genéricos con soporte español
# -----------------------------------------------

# Nombre corto: letras, números, espacios y caracteres españoles
ShortNameStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z0-9áéíóúüÁÉÍÓÚÜñÑ .,\-']+$",
    ),
    Field(description="Nombre corto (máx. 255 caracteres, letras y números)")
]

# Descripción larga: sin restricción de caracteres excepto longitud
DescriptionStr = Annotated[
    str,
    StringConstraints(max_length=2000),
    Field(description="Descripción larga (máx. 2000 caracteres)")
]

# URL de imagen
ImageURLStr = Annotated[
    HttpUrl,
    StringConstraints(max_length=500),
    Field(description="URL de imagen")
]


# -----------------------------------------------
# ⚡ Flags booleanos semánticos
# -----------------------------------------------

IsActiveFlag = Annotated[
    bool,
    Field(description="Indica si el registro está activo")
]
