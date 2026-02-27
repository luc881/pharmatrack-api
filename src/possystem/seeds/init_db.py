"""
possystem/seeds/init_db.py

Master runner — executes all seeders in the correct dependency order.

Usage:
    python -m possystem.seeds.init_db
"""
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
from possystem.seeds.seed_products_material_curacion import seed_material_curacion
from possystem.seeds.seed_products_suplementos import seed_suplementos
from possystem.seeds.seed_products_medicamentos import seed_medicamentos


def init_db():
    """Ejecuta todos los seeders del proyecto en orden correcto."""
    db: Session = SessionLocal()
    try:
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  🌱 Inicializando base de datos")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        # ── Seguridad ─────────────────────────────
        print("🔐 Permisos...")
        seed_permissions(db)

        print("\n👥 Roles...")
        seed_roles(db)

        # ── Configuración base ────────────────────
        print("\n🏪 Sucursales...")
        seed_branches(db)

        print("\n👤 Superusuario...")
        seed_superuser(db)

        # ── Catálogo ──────────────────────────────
        print("\n📂 Categorías de productos...")
        seed_product_categories(db)

        print("\n💊 Medicamentos...")
        seed_medicamentos(db)

        print("\n🧴 Suplementos...")
        seed_suplementos(db)

        print("\n🍬 Alimentos y bebidas...")
        seed_golosinas(db)

        print("\n🩹 Material de curación...")
        seed_material_curacion(db)

        print("\n💄 Salud y belleza...")
        seed_salud_belleza(db)

        print("\n🔧 Miscelánea y hogar...")
        seed_otros(db)

        print("\n🏥 Servicios farmacéuticos...")
        seed_servicios_medicos(db)

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  ✅ Base de datos inicializada correctamente")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante el seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()