import pytest
from passlib.context import CryptContext
from pharmatrack.utils.security import create_jwt_token  # ✅ import corregido
from datetime import timedelta

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def test_user_with_role_permissions_branch_auth(db_session, test_role_with_permissions_and_authentication, test_branch):
    from pharmatrack.models.users.orm import User
    id_role = test_role_with_permissions_and_authentication.id if test_role_with_permissions_and_authentication else 1
    id_branch = test_branch.id if test_branch else 1
    user_data = {
        "name": "testuser",
        "surname": "user surname",
        "email": "test@example.com",
        "password": bcrypt_context.hash("secureMpassword123"),
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2222222222",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M",
        "role_id": id_role,
        "branch_id": id_branch
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user_with_role_permissions_branch_auth):
    token = create_jwt_token(
        username=test_user_with_role_permissions_branch_auth.email,
        user_id=test_user_with_role_permissions_branch_auth.id,
        role=test_user_with_role_permissions_branch_auth.role.name,
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}