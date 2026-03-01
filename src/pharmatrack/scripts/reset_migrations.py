"""
Script de desarrollo para regenerar la migración inicial desde cero.
Uso: poetry run reset-migrations

Úsalo cuando:
- Cambiaste uno o más modelos ORM
- Quieres una migración inicial limpia (sin historial acumulado)
- Todavía estás en desarrollo y no hay datos reales que proteger

⚠️  SOLO para desarrollo — nunca usar en producción.
"""
import os
import shutil
import subprocess
from pathlib import Path
from pharmatrack.config import settings


def reset_migrations():
    if settings.is_production:
        print("❌ Este comando no puede ejecutarse en producción.")
        return

    # Buscar la carpeta versions/ relativa a donde está este script
    versions_path = Path(__file__).resolve().parent.parent.parent.parent / "migrations" / "versions"

    if not versions_path.exists():
        print(f"❌ No se encontró la carpeta: {versions_path}")
        print("   Asegúrate de haber corrido 'alembic init migrations' primero.")
        return

    print("⚠️  Regenerando migración inicial de desarrollo...")

    # 1. Bajar todas las migraciones activas (limpia alembic_version en la BD)
    print("🗑️  Bajando migraciones actuales...")
    subprocess.run(["alembic", "downgrade", "base"], check=True)

    # 2. Borrar todos los archivos de versiones
    print("🗑️  Eliminando archivos de versiones...")
    for archivo in versions_path.glob("*.py"):
        archivo.unlink()
    print(f"   Eliminados de: {versions_path}")

    # 3. Generar nueva migración inicial
    print("🔧 Generando nueva migración inicial...")
    subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "initial migration"],
        check=True
    )

    # 4. Aplicar la nueva migración
    print("🔧 Aplicando migración...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    # 5. Correr seeds
    print("🌱 Ejecutando seeds...")
    from pharmatrack.seeds.init_db import init_db
    init_db()

    print("✅ Migración inicial regenerada y seeds aplicados.")


if __name__ == "__main__":
    reset_migrations()