from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ..product_categories.schemas import ProductCategoryResponse
from ..products.schemas import ProductSimpleResponse


# =========================================================
# 🔹 Base schema
# =========================================================
class ProductMasterBase(BaseModel):
    name: str = Field(..., max_length=250)
    description: Optional[str] = Field(None, max_length=2000)


# =========================================================
# 🟢 Create
# =========================================================
class ProductMasterCreate(ProductMasterBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Paracetamol",
                "description": "Medicamento analgésico y antipirético."
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class ProductMasterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = Field(None, max_length=2000)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "description": "Analgésico suave ampliamente utilizado"
            }
        }
    )


# =========================================================
# 🔵 Simple Response
# =========================================================
class ProductMasterResponse(ProductMasterBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🧩 Detailed response
# =========================================================
class ProductMasterDetailsResponse(ProductMasterResponse):
    products: Optional[List[ProductSimpleResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 🔁 Forward references
# =========================================================
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..products.schemas import ProductSimpleResponse
