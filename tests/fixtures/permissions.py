import pytest



# --- Fixture for creating a sample permission ---

@pytest.fixture
def make_permission(db_session):
    from pharmatrack.models.permissions.orm import Permission
    def _make_permission(name: str) -> Permission:
        perm = Permission(name=name)
        db_session.add(perm)
        db_session.commit()
        db_session.refresh(perm)
        return perm
    return _make_permission