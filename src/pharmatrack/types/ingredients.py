from enum import Enum
from typing import Annotated, Optional
from pydantic import StringConstraints, Field, HttpUrl
from pydantic.types import NonNegativeFloat


# -------------------------------
# 🔤 String types
# -------------------------------

IngredientTitleStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=250,
        pattern=r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\-.,'\"() ]+$"
    ),
    Field(description="Título del producto")
]

IngredientDescriptionStr = Annotated[
    str,
    StringConstraints(
        max_length=2000
    ),
    Field(description="Descripción del producto")
]