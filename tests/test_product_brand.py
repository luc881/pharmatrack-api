import pytest
from pharmatrack.api.routes.product_brand import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
prodBrand_get, prodBrand_post, prodBrand_put, prodBrand_patch, prodBrand_delete = route_client_factory(client, "productsbrand")


# =========================================================
# Fixtures — incluyen slug
# =========================================================

@pytest.fixture
def test_product_brand(db_session):
    from pharmatrack.models.product_brand.orm import ProductBrand
    from pharmatrack.utils.slugify import slugify
    brand = ProductBrand(
        name="Bayer",
        slug=slugify("Bayer"),
        logo="http://example.com/bayer_logo.jpg",
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def another_product_brand(db_session):
    from pharmatrack.models.product_brand.orm import ProductBrand
    from pharmatrack.utils.slugify import slugify
    brand = ProductBrand(
        name="Pfizer",
        slug=slugify("Pfizer"),
        logo="http://example.com/pfizer_logo.jpg",
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def brand_no_logo(db_session):
    from pharmatrack.models.product_brand.orm import ProductBrand
    from pharmatrack.utils.slugify import slugify
    brand = ProductBrand(
        name="NoLogoBrand",
        slug=slugify("NoLogoBrand"),
        logo=None,
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


# =========================================================
# 🔹 GET /
# =========================================================

def test_read_all_empty(auth_headers):
    response = prodBrand_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_read_all_with_data(auth_headers, test_product_brand):
    response = prodBrand_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    ids = [b["id"] for b in data["data"]]
    assert test_product_brand.id in ids


def test_read_all_no_auth():
    response = prodBrand_get()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 GET /{brand_id}
# =========================================================

def test_read_brand_by_id(auth_headers, test_product_brand):
    response = prodBrand_get(str(test_product_brand.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_product_brand.id
    assert data["name"] == test_product_brand.name


def test_read_brand_by_id_not_found(auth_headers):
    response = prodBrand_get("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_read_brand_by_id_no_auth(test_product_brand):
    response = prodBrand_get(str(test_product_brand.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 GET /search/
# Devuelve PaginatedResponse — acceder con data["data"]
# =========================================================

def test_search_brands_by_name(auth_headers, test_product_brand):
    response = prodBrand_get("search/?name=Bayer", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    ids = [b["id"] for b in data["data"]]
    assert test_product_brand.id in ids


def test_search_brands_by_name_no_results(auth_headers):
    response = prodBrand_get("search/?name=ZZZ_NOT_EXIST", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 0


def test_search_brands_has_logo_true(auth_headers, test_product_brand):
    response = prodBrand_get("search/?has_logo=true", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(b["logo"] is not None for b in data["data"])


def test_search_brands_has_logo_false(auth_headers, brand_no_logo):
    response = prodBrand_get("search/?has_logo=false", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    ids = [b["id"] for b in response.json()["data"]]
    assert brand_no_logo.id in ids


def test_search_brands_no_auth():
    response = prodBrand_get("search/?name=test")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_brand(auth_headers):
    response = prodBrand_post(json={"name": "TestBrand", "logo": "http://example.com/logo.jpg"}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "TestBrand"
    assert data["logo"] == "http://example.com/logo.jpg"


def test_create_brand_duplicate(auth_headers, test_product_brand):
    response = prodBrand_post(json={"name": test_product_brand.name, "logo": "http://x.com/logo.jpg"}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_create_brand_missing_name(auth_headers):
    response = prodBrand_post(json={"logo": "http://x.com/logo.jpg"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_brand_no_auth():
    response = prodBrand_post(json={"name": "NoAuthBrand", "logo": "http://x.com/logo.jpg"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 PUT /{brand_id}
# =========================================================

def test_update_brand(auth_headers, test_product_brand):
    response = prodBrand_put(
        str(test_product_brand.id),
        json={"name": "UpdatedBrandName", "logo": "http://x.com/updated.jpg"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "UpdatedBrandName"
    assert data["logo"] == "http://x.com/updated.jpg"


def test_update_brand_duplicate_name(auth_headers, test_product_brand, another_product_brand):
    response = prodBrand_put(
        str(test_product_brand.id),
        json={"name": another_product_brand.name},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "is already in use." in response.json()["detail"]


def test_update_brand_not_found(auth_headers):
    response = prodBrand_put("9999", json={"name": "Ghost"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_update_brand_no_auth(test_product_brand):
    response = prodBrand_put(str(test_product_brand.id), json={"name": "NoAuth"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 DELETE /{brand_id}
# =========================================================

def test_delete_brand(auth_headers, test_product_brand):
    response = prodBrand_delete(str(test_product_brand.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_brand_verify_gone(auth_headers, test_product_brand):
    prodBrand_delete(str(test_product_brand.id), headers=auth_headers)
    response = prodBrand_get(str(test_product_brand.id), headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_brand_not_found(auth_headers):
    response = prodBrand_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_delete_brand_no_auth(test_product_brand):
    response = prodBrand_delete(str(test_product_brand.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED