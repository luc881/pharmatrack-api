from typing import Optional, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Literal

# =========================================================
# 🔹 Enum de unidades de medida
# =========================================================

class UnitEnum(str, Enum):
    mg = "mg"
    g = "g"
    ml = "ml"
    IU = "IU"
    mcg = "mcg"
    mmol = "mmol"
    percent = "%"


# =========================================================
# 🔹 Base schema
# =========================================================

class ProductIngredientBase(BaseModel):
    ingredient_id: int = Field(..., description="Ingredient ID")
    amount: Optional[float] = Field(
        None, description="Numeric dose amount (e.g., 500)"
    )
    unit: Optional[UnitEnum] = Field(
        None, description="Unit of measurement"
    )


# =========================================================
# 🟢 Create schema
# =========================================================

class ProductIngredientCreate(ProductIngredientBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "amount": 500,
                "unit": "mg"
            }
        }
    )


# =========================================================
# 🟡 Update schema
# =========================================================

class ProductIngredientUpdate(BaseModel):
    amount: Optional[float] = Field(None, description="Updated numeric dose")
    unit: Optional[UnitEnum] = Field(None, description="Updated unit")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 650,
                "unit": "mg"
            }
        }
    )


# =========================================================
# 🔵 Pivot table Response
# =========================================================

class ProductIngredientResponse(ProductIngredientBase):
    product_id: int
    ingredient: Optional["IngredientResponse"] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "product_id": 20,
                "ingredient_id": 1,
                "amount": 500,
                "unit": "mg",
                "ingredient": {
                    "id": 1,
                    "name": "Ibuprofeno"
                }
            }
        }
    )


# =========================================================
# 🧩 Embedded ingredient detail (for Product details)
# =========================================================

class ProductIngredientAmount(BaseModel):
    ingredient_id: int
    amount: Optional[float] = None
    unit: Optional[UnitEnum] = None

    # Full ingredient relationship
    ingredient: Optional["IngredientResponse"] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "amount": 500,
                "unit": "mg",
                "ingredient": {
                    "id": 1,
                    "name": "Ibuprofeno"
                }
            }
        }
    )


# =========================================================
# 🔁 Forward references
# =========================================================

if TYPE_CHECKING:
    from ..ingredients.schemas import IngredientResponse