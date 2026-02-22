from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal

from possystem.seeds.seed_permissions import seed_permissions
from possystem.seeds.seed_roles import seed_roles
from possystem.seeds.seed_product_categories import seed_product_categories
from possystem.seeds.seed_superuser import seed_superuser
from possystem.seeds.seed_branches import seed_branches
from possystem.seeds.seed_products_alimentos import seed_golosinas
from possystem.seeds.seed_products_otros import seed_otros
from possystem.seeds.seed_products_saludybelleza import seed_salud_belleza
from possystem.seeds.seed_products_serviciosmedicos import seed_servicios_medicos
from possystem.seeds.seed_products_equipomedico import seed_material_curacion


def init_db():
    """Ejecuta todos los seeders del proyecto en orden correcto."""
    db: Session = SessionLocal()
    try:
        print("🔹 Iniciando seeding de permisos...")
        seed_permissions(db)

        print("🔹 Iniciando seeding de roles...")
        seed_roles(db)

        print("🔹 Iniciando seeding de categorías de productos...")
        seed_product_categories(db)

        print("🔹 Iniciando seeding de sucursales...")
        seed_branches(db)

        print("🔹 Iniciando seeding de alimentos y bebidas...")
        seed_golosinas(db)

        print("🔹 Seeding de productos de otros...")
        seed_otros(db)

        print("🔹 Seeding de productos de salud y belleza...")
        seed_salud_belleza(db)

        print("🔹 Seeding de servicios médicos...")
        seed_servicios_medicos(db)

        print("🔹 Seeding de material de curación...")
        seed_material_curacion(db)

        print("🔹 Creando superusuario...")
        seed_superuser(db)



        print("🎉 Base de datos inicializada correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
