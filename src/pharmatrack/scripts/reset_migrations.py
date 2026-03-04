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
import subprocess
from pathlib import Path
from pharmatrack.config import settings


def reset_migrations():
    if settings.is_production:
        print("❌ Este comando no puede ejecutarse en producción.")
        return

    versions_path = Path(__file__).resolve().parent.parent.parent.parent / "migrations" / "versions"

    if not versions_path.exists():
        print(f"❌ No se encontró la carpeta: {versions_path}")
        print("   Asegúrate de haber corrido 'alembic init migrations' primero.")
        return

    print("⚠️  Regenerando migración inicial de desarrollo...")

    # 1. Borrar todas las tablas directamente vía SQL (más confiable que alembic downgrade,
    #    ya que downgrade falla si los constraints autogenerados no tienen nombre).
    print("🗑️  Eliminando tablas de la base de datos...")
    _drop_all_tables()

    # 2. Borrar todos los archivos de versiones
    print("🗑️  Eliminando archivos de versiones...")
    for archivo in versions_path.glob("*.py"):
        archivo.unlink()
    print(f"   Eliminados de: {versions_path}")

    alembic_env = {**os.environ, "DATABASE_URL": settings.database_url}

    # 3. Generar nueva migración inicial
    print("🔧 Generando nueva migración inicial...")
    subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "initial migration"],
        check=True,
        env=alembic_env,
    )

    # 4. Aplicar la nueva migración
    print("🔧 Aplicando migración...")
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=alembic_env)

    # 5. Correr seeds
    print("🌱 Ejecutando seeds...")
    from pharmatrack.seeds.init_db import init_db
    init_db()

    print("✅ Migración inicial regenerada y seeds aplicados.")


def _drop_all_tables():
    """
    Elimina todas las tablas del schema public (incluyendo alembic_version)
    usando CASCADE para respetar foreign keys sin importar el orden.
    Evita el problema de constraints sin nombre que rompe 'alembic downgrade base'.
    """
    from sqlalchemy import text
    from pharmatrack.db.session import _get_engine

    with _get_engine().connect() as conn:
        result = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        tables = [row[0] for row in result]

        if not tables:
            print("   No hay tablas que eliminar.")
            return

        tables_str = ", ".join(f'"{t}"' for t in tables)
        conn.execute(text(f"DROP TABLE IF EXISTS {tables_str} CASCADE"))
        conn.commit()
        print(f"   Eliminadas {len(tables)} tablas: {', '.join(tables)}")


if __name__ == "__main__":
    reset_migrations()