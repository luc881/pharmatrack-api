"""Base de datos limpia para las pruebas de punta a punta (Playwright).

Borra y vuelve a crear la base que dice DATABASE_URL. Solo acepta una base
cuyo nombre termine en `_e2e`, para no poder borrar nunca la de desarrollo
ni la de producción por un error de configuración.

Uso (lo corre playwright.config.js del dashboard antes de levantar el API):
    DATABASE_URL=postgresql://postgres:postgres@localhost/pharmatrack_e2e \
        poetry run python scripts/e2e_reset_db.py
"""
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main() -> None:
    url = make_url(os.environ["DATABASE_URL"])
    name = url.database or ""
    if not name.endswith("_e2e"):
        sys.exit(f"Me niego a borrar «{name}»: la base de pruebas debe terminar en _e2e")

    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :name AND pid <> pg_backend_pid()"
        ), {"name": name})
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        conn.execute(text(f'CREATE DATABASE "{name}"'))
        # el frontend lee todas las fechas como UTC (igual que Railway)
        conn.execute(text(f"ALTER DATABASE \"{name}\" SET timezone TO 'UTC'"))
    admin.dispose()
    print(f"Base {name} lista")


if __name__ == "__main__":
    main()
