import pytest

# --- Fixture for creating a sample product master ---

@pytest.fixture
def test_product_master(db_session, test_product_category):
    from pharmatrack.models.product_master.orm import ProductMaster
    product_master_data = {
                "name": "Paracetamol",
                "description": "Medicamento para aliviar el dolor y reducir la fiebre",
                "product_category_id": test_product_category.id
            }
    product_master = ProductMaster(**product_master_data)
    db_session.add(product_master)
    db_session.commit()
    db_session.refresh(product_master)
    return product_master

@pytest.fixture
def another_product_master(db_session, test_product_category):
    from pharmatrack.models.product_master.orm import ProductMaster
    product_master_data = {
                "name": "Ibuprofeno",
                "description": "Medicamento antiinflamatorio y analgésico",
                "product_category_id": test_product_category.id
            }
    product_master = ProductMaster(**product_master_data)
    db_session.add(product_master)
    db_session.commit()
    db_session.refresh(product_master)
    return product_master