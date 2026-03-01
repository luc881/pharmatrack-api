"""
Script de desarrollo para resetear la base de datos y re-sembrar datos.
Uso: poetry run reset-db

⚠️  SOLO para desarrollo — nunca usar en producción.
"""
import subprocess
from pharmatrack.config import settings


def reset_db():
    if settings.is_production:
        print("❌ Este comando no puede ejecutarse en producción.")
        return

    print("⚠️  Reseteando base de datos de desarrollo...")

    # 1. Bajar todas las migraciones (elimina todas las tablas)
    print("🗑️  Eliminando tablas...")
    subprocess.run(["alembic", "downgrade", "base"], check=True)

    # 2. Aplicar todas las migraciones (recrea las tablas)
    print("🔧 Recreando tablas...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    # 3. Correr seeds
    print("🌱 Ejecutando seeds...")
    from pharmatrack.seeds.init_db import init_db
    init_db()

    print("✅ Base de datos reseteada y seeds aplicados.")


if __name__ == "__main__":
    reset_db()