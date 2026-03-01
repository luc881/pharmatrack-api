# Import schemas first
from .roles.schemas import RoleWithPermissions, RoleResponse
from .permissions.schemas import PermissionWithRoles, PermissionResponse
from .branches.schemas import BranchWithUsersResponse, BranchResponse
from .users.schemas import UserResponse, UserDetailsResponse
from .products.schemas import ProductResponse, ProductDetailsResponse
from .product_batch.schemas import ProductBatchDetailsResponse, ProductBatchResponse
from .product_brand.schemas import ProductBrandResponse
from .product_master.schemas import ProductMasterResponse
from .ingredients.schemas import IngredientResponse

# =========================================================
# 🔧 Resolve forward references
# =========================================================
RoleWithPermissions.model_rebuild()
PermissionWithRoles.model_rebuild()
BranchWithUsersResponse.model_rebuild()
BranchResponse.model_rebuild()
UserResponse.model_rebuild()
UserDetailsResponse.model_rebuild()

ProductResponse.model_rebuild()
ProductDetailsResponse.model_rebuild()

ProductBatchResponse.model_rebuild()
ProductBatchDetailsResponse.model_rebuild()

ProductBrandResponse.model_rebuild()
ProductMasterResponse.model_rebuild()
IngredientResponse.model_rebuild()

# =========================================================
# 🧩 Import ORM models
# =========================================================
from .users.orm import User
from .roles.orm import Role
from .permissions.orm import Permission
from .branches.orm import Branch
from .product_categories.orm import ProductCategory
from .products.orm import Product
from .sales.orm import Sale
from .sale_payments.orm import SalePayment
from .sale_details.orm import SaleDetail
from .refund_products.orm import RefundProduct
from .suppliers.orm import Supplier
from .purchases.orm import Purchase
from .purchase_details.orm import PurchaseDetail
from .product_batch.orm import ProductBatch
from .sale_batch_usage.orm import SaleBatchUsage
from .product_master.orm import ProductMaster
from .product_brand.orm import ProductBrand
from .ingredients.orm import Ingredient

# when you have all coorect you can try
# # src/pharmatrack/models/__init__.py
# import pkgutil
# import importlib
# from .session import Base  # Your SQLAlchemy declarative base
# from pydantic import BaseModel
#
# # -------------------------------------------------
# # 1️⃣ Automatically import all submodules inside models
# # -------------------------------------------------
# package_name = __name__
#
# for finder, name, ispkg in pkgutil.iter_modules(__path__):
#     full_module_name = f"{package_name}.{name}"
#     module = importlib.import_module(full_module_name)
#
#     # Optional: If the module has an 'orm' submodule, import it too
#     try:
#         importlib.import_module(f"{full_module_name}.orm")
#     except ModuleNotFoundError:
#         pass
#
# # -------------------------------------------------
# # 2️⃣ Rebuild all Pydantic forward references
# # -------------------------------------------------
# for subclass in BaseModel.__subclasses__():
#     try:
#         subclass.model_rebuild()
#     except Exception:
#         # Ignore models that don't have forward references
#         pass
