import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# =========================================================
# 🔹 Importar Base con todos los modelos
# =========================================================
from pharmatrack.db.session import Base

# Importar TODOS los modelos para que Alembic los detecte
from pharmatrack.models.permissions.orm import Permission
from pharmatrack.models.roles.orm import Role
from pharmatrack.models.role_has_permissions.orm import role_has_permissions
from pharmatrack.models.users.orm import User
from pharmatrack.models.branches.orm import Branch
from pharmatrack.models.ingredients.orm import Ingredient
from pharmatrack.models.product_categories.orm import ProductCategory
from pharmatrack.models.product_master.orm import ProductMaster
from pharmatrack.models.product_brand.orm import ProductBrand
from pharmatrack.models.products.orm import Product
from pharmatrack.models.product_has_ingredients.orm import ProductHasIngredient
from pharmatrack.models.product_batch.orm import ProductBatch
from pharmatrack.models.sales.orm import Sale
from pharmatrack.models.sale_details.orm import SaleDetail
from pharmatrack.models.sale_payments.orm import SalePayment
from pharmatrack.models.sale_batch_usage.orm import SaleBatchUsage
from pharmatrack.models.refund_products.orm import RefundProduct
from pharmatrack.models.suppliers.orm import Supplier
from pharmatrack.models.purchases.orm import Purchase
from pharmatrack.models.purchase_details.orm import PurchaseDetail

# =========================================================
# 🔹 Config de Alembic
# =========================================================
config = context.config

# Leer DATABASE_URL directo del entorno (evita pasar por pydantic-settings)
database_url = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("DATABASE_PRIVATE_URL")
    or os.environ.get("POSTGRES_URL")
)

if not database_url:
    available = [k for k in os.environ if "DATA" in k or "PG" in k or "POSTGRES" in k]
    raise RuntimeError(f"No database URL found. DB-related env vars available: {available}")

config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# =========================================================
# 🔹 Modo offline (genera SQL sin conectarse a la BD)
# =========================================================
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# 🔹 Modo online (se conecta a la BD y aplica migraciones)
# =========================================================
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()