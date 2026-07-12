import pytest



# --- Fixture for creating a sample permission ---


@pytest.fixture
def test_role(db_session):
    from pharmatrack.models.roles.orm import Role
    role = Role(name="admin")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def test_role_with_permissions(db_session, test_permission):
    from pharmatrack.models.roles.orm import Role
    role = Role(name="manager")
    role.permissions.append(test_permission)  # Same session, no error
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def test_role_with_permissions_and_authentication(db_session, make_permission):
    from pharmatrack.models.roles.orm import Role
    # Misma lista que el seed real: evita que se desactualice al agregar módulos
    from pharmatrack.seeds.seed_permissions import PERMISSIONS
    role = Role(name="manager")
    role.permissions.extend(make_permission(name) for name in PERMISSIONS)

    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role
