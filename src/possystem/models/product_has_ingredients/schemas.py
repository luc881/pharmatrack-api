from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

# =========================================================
# 🔹 Base
# =========================================================
class ProductIngredientBase(BaseModel):
    ingredient_id: int = Field(..., description="Ingredient ID")
    amount: Optional[str] = Field(
        None, max_length=50, description="Amount of ingredient (e.g., '500 mg')"
    )


# =========================================================
# 🟢 Create
# =========================================================
class ProductIngredientCreate(ProductIngredientBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "amount": "500 mg"
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class ProductIngredientUpdate(BaseModel):
    amount: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "650 mg"
            }
        }
    )


# =========================================================
# 🔵 Response (pivot table)
# =========================================================
class ProductIngredientResponse(ProductIngredientBase):
    product_id: int
    ingredient: Optional["IngredientResponse"] = None  # relación

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "product_id": 20,
                "ingredient_id": 1,
                "amount": "500 mg",
                "ingredient": {
                    "id": 1,
                    "name": "Ibuprofeno"
                }
            }
        }
    )


# =========================================================
# 🧩 Para ProductDetailsResponse
# =========================================================
class ProductIngredientAmount(BaseModel):
    ingredient_id: int
    amount: Optional[str] = None

    # RELACIÓN COMPLETA
    ingredient: Optional["IngredientResponse"] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "amount": "500 mg",
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
