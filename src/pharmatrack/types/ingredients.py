from typing import Annotated
from pydantic import StringConstraints, Field
from pharmatrack.types.common import DescriptionStr

# DescriptionStr reutilizado desde common
IngredientDescriptionStr = DescriptionStr  # alias semántico


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
    Field(description="Nombre del ingrediente activo")
]