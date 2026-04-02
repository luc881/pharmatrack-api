import pytest
from pharmatrack.api.routes.product_categories import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
productCat_get, productCat_post, productCat_put, productCat_patch, productCat_delete = route_client_factory(client, "productscategories")


# =========================================================
# Fixtures — con slug generado manualmente
# =========================================================

@pytest.fixture
def test_product_category(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    cat = ProductCategory(
        name="Analgésicos",
        slug=slugify("Analgésicos"),
        image="http://example.com/analgesicos.png",
        is_active=True,
        parent_id=None,
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def another_product_category(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    cat = ProductCategory(
        name="Antibióticos",
        slug=slugify("Antibióticos"),
        image="http://example.com/antibioticos.png",
        is_active=True,
        parent_id=None,
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def category_root(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    root = ProductCategory(
        name="Medicamentos",
        slug=slugify("Medicamentos"),
        image=None,
        is_active=True,
        parent_id=None,
    )
    db_session.add(root)
    db_session.commit()
    db_session.refresh(root)
    return root


@pytest.fixture
def category_child(db_session, category_root):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.category_slug import build_category_slug
    slug = build_category_slug("Analgésicos", category_root.id, db_session)
    child = ProductCategory(
        name="Analgésicos",
        slug=slug,
        image=None,
        is_active=True,
        parent_id=category_root.id,
    )
    db_session.add(child)
    db_session.commit()
    db_session.refresh(child)
    return child


@pytest.fixture
def category_subchild(db_session, category_child):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.category_slug import build_category_slug
    slug = build_category_slug("Paracetamol", category_child.id, db_session)
    subchild = ProductCategory(
        name="Paracetamol",
        slug=slug,
        image=None,
        is_active=True,
        parent_id=category_child.id,
    )
    db_session.add(subchild)
    db_session.commit()
    db_session.refresh(subchild)
    return subchild


# =========================================================
# 🔹 GET /  — PaginatedResponse
# =========================================================

def test_read_all_empty(auth_headers):
    response = productCat_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_read_all_with_data(test_product_category, auth_headers):
    response = productCat_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    ids = [c["id"] for c in data["data"]]
    assert test_product_category.id in ids
    cat = next(c for c in data["data"] if c["id"] == test_product_category.id)
    assert cat["name"] == "Analgésicos"
    assert cat["image"] == "http://example.com/analgesicos.png"


def test_read_all_no_auth():
    response = productCat_get()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 GET /{category_id}
# =========================================================

def test_read_one(test_product_category, auth_headers):
    response = productCat_get(str(test_product_category.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_product_category.id
    assert data["name"] == test_product_category.name
    assert data["image"] == test_product_category.image
    assert data["is_active"] == test_product_category.is_active


def test_read_one_not_found(auth_headers):
    response = productCat_get("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Category not found."


# =========================================================
# 🔹 GET /tree  — lista, no paginada
# =========================================================

def test_get_category_tree_empty(auth_headers):
    response = productCat_get("tree", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_category_tree(category_root, category_child, category_subchild, auth_headers):
    response = productCat_get("tree", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    root = data[0]
    assert root["name"] == "Medicamentos"
    assert root["parent_id"] is None
    assert len(root["children"]) == 1

    child = root["children"][0]
    assert child["name"] == "Analgésicos"
    assert child["parent_id"] == category_root.id
    assert len(child["children"]) == 1

    subchild = child["children"][0]
    assert subchild["name"] == "Paracetamol"
    assert subchild["parent_id"] == category_child.id
    assert subchild["children"] == []


# =========================================================
# 🔹 GET /roots  — PaginatedResponse
# =========================================================

def test_get_root_categories_empty(auth_headers):
    response = productCat_get("roots", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0


def test_get_root_categories(category_root, category_child, auth_headers):
    response = productCat_get("roots", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["name"] == "Medicamentos"
    assert data["data"][0]["parent_id"] is None


def test_get_multiple_root_categories(db_session, auth_headers):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    root1 = ProductCategory(name="Medicamentos", slug=slugify("Medicamentos"), parent_id=None, is_active=True)
    root2 = ProductCategory(name="Papelería", slug=slugify("Papelería"), parent_id=None, is_active=True)
    db_session.add_all([root1, root2])
    db_session.commit()

    response = productCat_get("roots", headers=auth_headers)
    data = response.json()
    names = {c["name"] for c in data["data"]}
    assert "Medicamentos" in names
    assert "Papelería" in names


def test_roots_does_not_return_children(category_root, category_child, auth_headers):
    response = productCat_get("roots", headers=auth_headers)
    data = response.json()
    ids = [c["id"] for c in data["data"]]
    assert category_child.id not in ids


# =========================================================
# 🔹 GET /{category_id}/tree
# =========================================================

def test_get_subtree(category_root, category_child, category_subchild, auth_headers):
    response = productCat_get(f"{category_root.id}/tree", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category_root.id
    assert data["name"] == "Medicamentos"
    assert len(data["children"]) == 1

    child = data["children"][0]
    assert child["name"] == "Analgésicos"
    assert len(child["children"]) == 1

    subchild = child["children"][0]
    assert subchild["name"] == "Paracetamol"
    assert subchild["children"] == []


def test_get_subtree_leaf(category_subchild, auth_headers):
    response = productCat_get(f"{category_subchild.id}/tree", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category_subchild.id
    assert data["children"] == []


def test_get_subtree_not_found(auth_headers):
    response = productCat_get("9999/tree", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Category not found."


def test_subtree_children_unique(category_root, category_child, category_subchild, auth_headers):
    response = productCat_get(f"{category_root.id}/tree", headers=auth_headers)
    data = response.json()
    child_ids = [c["id"] for c in data["children"]]
    assert len(child_ids) == len(set(child_ids))


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_category(auth_headers):
    payload = {"name": "New Category", "image": "http://example.com/new.png", "is_active": True}
    response = productCat_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["image"] == payload["image"]
    assert data["is_active"] == payload["is_active"]


def test_create_category_with_parent(category_root, auth_headers):
    payload = {"name": "Analgésicos", "image": None, "is_active": True, "parent_id": category_root.id}
    response = productCat_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Analgésicos"
    assert data["parent_id"] == category_root.id


def test_create_category_parent_not_found(auth_headers):
    payload = {"name": "Vitaminas", "image": None, "is_active": True, "parent_id": 9999}
    response = productCat_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Parent category not found."


def test_create_category_duplicate(test_product_category, auth_headers):
    # Mismo nombre en mismo nivel (root) → mismo slug → duplicado
    payload = {"name": test_product_category.name, "image": None, "is_active": True}
    response = productCat_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_create_category_no_auth():
    response = productCat_post(json={"name": "Sin auth", "is_active": True})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 PUT /{category_id}
# =========================================================

def test_update_category(test_product_category, auth_headers):
    payload = {"name": "Updated Category", "image": "http://example.com/updated.png", "is_active": False}
    response = productCat_put(str(test_product_category.id), json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Category"
    assert data["image"] == payload["image"]
    assert data["is_active"] is False


def test_update_category_not_found(auth_headers):
    response = productCat_put("9999", json={"name": "Ghost"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product category not found."


def test_update_category_parent(category_root, test_product_category, auth_headers):
    response = productCat_put(
        str(test_product_category.id),
        json={"parent_id": category_root.id},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["parent_id"] == category_root.id


def test_update_category_self_parent(test_product_category, auth_headers):
    response = productCat_put(
        str(test_product_category.id),
        json={"parent_id": test_product_category.id},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Category cannot be its own parent."


def test_update_category_parent_not_found(test_product_category, auth_headers):
    response = productCat_put(str(test_product_category.id), json={"parent_id": 9999}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Parent category not found."


def test_update_category_cycle(category_root, category_child, category_subchild, auth_headers):
    # Intentar hacer root hijo de subchild → ciclo
    response = productCat_put(
        str(category_root.id),
        json={"parent_id": category_subchild.id},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_category_name_conflict(test_product_category, another_product_category, auth_headers):
    response = productCat_put(
        str(test_product_category.id),
        json={"name": another_product_category.name},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_category_no_auth(test_product_category):
    response = productCat_put(str(test_product_category.id), json={"name": "Sin auth"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 DELETE /{category_id}
# =========================================================

def test_delete_category(test_product_category, auth_headers):
    response = productCat_delete(str(test_product_category.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    get_response = productCat_get(headers=auth_headers)
    ids = [c["id"] for c in get_response.json()["data"]]
    assert test_product_category.id not in ids


def test_delete_category_with_children(category_root, category_child, auth_headers):
    response = productCat_delete(str(category_root.id), headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_leaf_category(category_subchild, auth_headers):
    response = productCat_delete(str(category_subchild.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_category_not_found(auth_headers):
    response = productCat_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product category not found."


def test_delete_category_no_auth(test_product_category):
    response = productCat_delete(str(test_product_category.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED