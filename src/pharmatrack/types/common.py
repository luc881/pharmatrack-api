"""
Tipos Pydantic reutilizables en toda la API.
Importar desde aquí en lugar de redefinir en cada módulo.
"""
from datetime import date
from typing import Annotated, Optional
from pydantic import StringConstraints, Field, HttpUrl
from pydantic.functional_validators import AfterValidator
from pydantic.types import NonNegativeFloat


# -----------------------------------------------
# 📊 Porcentajes
# -----------------------------------------------

TaxPercentage = Annotated[
    Optional[NonNegativeFloat],
    Field(le=100, description="Porcentaje de impuesto (0–100)")
]

DiscountPercentage = Annotated[
    Optional[NonNegativeFloat],
    Field(le=100, description="Porcentaje de descuento máximo permitido (0–100)")
]


# -----------------------------------------------
# 🔤 Strings genéricos
# -----------------------------------------------

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
# 📅 Fechas validadas
# -----------------------------------------------

def _check_future_or_present(v: date) -> date:
    if v < date.today():
        raise ValueError("La fecha de vencimiento no puede ser una fecha pasada")
    return v

FutureOrPresentDate = Annotated[
    date,
    AfterValidator(_check_future_or_present),
    Field(description="Fecha de vencimiento (hoy o futura)"),
]
