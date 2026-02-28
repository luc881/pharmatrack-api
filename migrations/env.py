from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# =========================================================
# 🔹 Importar settings y Base con todos los modelos
# =========================================================
from possystem.config import settings
from possystem.db.session import Base

# Importar TODOS los modelos para que Alembic los detecte
# Si no están importados aquí, Alembic no generará sus migraciones
from possystem.models.permissions.orm import Permission
from possystem.models.roles.orm import Role
from possystem.models.role_has_permissions.orm import role_has_permissions
from possystem.models.users.orm import User
from possystem.models.branches.orm import Branch
from possystem.models.ingredients.orm import Ingredient
from possystem.models.product_categories.orm import ProductCategory
from possystem.models.product_master.orm import ProductMaster
from possystem.models.product_brand.orm import ProductBrand
from possystem.models.products.orm import Product
from possystem.models.product_has_ingredients.orm import ProductHasIngredient
from possystem.models.product_batch.orm import ProductBatch
from possystem.models.sales.orm import Sale
from possystem.models.sale_details.orm import SaleDetail
from possystem.models.sale_payments.orm import SalePayment
from possystem.models.sale_batch_usage.orm import SaleBatchUsage
from possystem.models.refund_products.orm import RefundProduct
from possystem.models.suppliers.orm import Supplier
from possystem.models.purchases.orm import Purchase
from possystem.models.purchase_details.orm import PurchaseDetail

# =========================================================
# 🔹 Config de Alembic
# =========================================================
config = context.config

# Inyectar DATABASE_URL desde settings (sobreescribe alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Apuntar al metadata de tu Base para autogenerar migraciones
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