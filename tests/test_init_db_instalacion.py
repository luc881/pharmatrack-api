"""Otra instalación (SEED_CATALOG=false) arranca solo con permisos, roles,
sucursal y admin; el admin nunca usa una contraseña fija del código."""
from pharmatrack.config import settings
from pharmatrack.models.animals.orm import AnimalGroup
from pharmatrack.models.articles.orm import Article
from pharmatrack.models.product_categories.orm import ProductCategory
from pharmatrack.models.products.orm import Product
from pharmatrack.models.roles.orm import Role
from pharmatrack.models.users.orm import User
from pharmatrack.seeds import init_db as init_db_module
from pharmatrack.seeds.seed_superuser import pwd_context

from .utils import TestingSessionLocal


def _run(monkeypatch, password):
    monkeypatch.setattr(init_db_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(settings, "seed_catalog", False)
    monkeypatch.setattr(settings, "superuser_email", "admin@veterinaria.test")
    monkeypatch.setattr(settings, "superuser_password", password)
    init_db_module.init_db()


def test_sin_catalogo_solo_lo_indispensable(db_session, monkeypatch):
    _run(monkeypatch, "clave-de-prueba")

    assert db_session.query(Role).filter_by(name="admin").first()
    admin = db_session.query(User).filter_by(email="admin@veterinaria.test").one()
    assert pwd_context.verify("clave-de-prueba", admin.password)
    for model in (ProductCategory, AnimalGroup, Product, Article):
        assert db_session.query(model).count() == 0, model.__name__


def test_admin_sin_contrasena_genera_una_al_azar(db_session, monkeypatch):
    _run(monkeypatch, "")

    admin = db_session.query(User).filter_by(email="admin@veterinaria.test").one()
    assert not pwd_context.verify("1278972", admin.password)
