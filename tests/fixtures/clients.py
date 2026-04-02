import pytest

@pytest.fixture
def test_client(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.clients.orm import Client
    client_data = {
                "name": "Carlos",
                "surname": "Ramírez",
                "full_name": "Carlos Ramírez",
                "phone": "5559876543",
                "email": "carlos.ramirez@example.com",
                "type_client": 1,
                "type_document": "DNI",
                "n_document": "87654321",
                "birth_date": "1990-05-20T00:00:00",
                "gender": "M",
                "user_id": test_user_with_role_permissions_branch_auth.id,
                "branch_id": test_branch.id,
                "state": 1,
                "address": "Av. Siempre Viva 742",
                "region": "Lima",
                "provincia": "Lima",
                "distrito": "Miraflores"
            }
    client = Client(**client_data)
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client

@pytest.fixture
def another_test_client(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.clients.orm import Client
    client_data = {
                "name": "Ana",
                "surname": "García",
                "full_name": "Ana García",
                "phone": "5551234567",
                "email": "laura.garcia@example.com",
                "type_client": 2,
                "type_document": "RUC",
                "n_document": "20123456789",
                "birth_date": "1985-10-15T00:00:00",
                "gender": "F",
                "user_id": test_user_with_role_permissions_branch_auth.id,
                "branch_id": test_branch.id,
                "state": 1,
                "address": "Calle Falsa 123",
                "region": "Lima",
                "provincia": "Lima",
                "distrito": "Surco"
            }
    client = Client(**client_data)
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client