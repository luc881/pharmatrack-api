import pytest

# --- Fixture for creating a sample product master ---

@pytest.fixture
def test_product_brand(db_session):
    from pharmatrack.models.product_brand.orm import ProductBrand
    product_brand_data = {
                "name": "Bayer",
                "logo": "http://example.com/bayer_logo.jpg",
            }
    product_brand = ProductBrand(**product_brand_data)
    db_session.add(product_brand)
    db_session.commit()
    db_session.refresh(product_brand)
    return product_brand

@pytest.fixture
def another_product_brand(db_session):
    from pharmatrack.models.product_brand.orm import ProductBrand
    product_brand_data = {
                "name": "Pfizer",
                "logo": "http://example.com/pfizer_logo.jpg",
            }
    product_brand = ProductBrand(**product_brand_data)
    db_session.add(product_brand)
    db_session.commit()
    db_session.refresh(product_brand)
    return product_brand