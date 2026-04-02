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
    role = Role(name="manager")
    perms = [make_permission(name) for name in [
        "users.read", "users.create", "users.update", "users.delete",
        "branches.read", "branches.create", "branches.update", "branches.delete",
        "permissions.read", "permissions.create", "permissions.update", "permissions.delete",
        "roles.read", "roles.create", "roles.update", "roles.delete",
        "units.read", "units.create", "units.update", "units.delete",
        "warehouses.read", "warehouses.create", "warehouses.update", "warehouses.delete",
        "products.read", "products.create", "products.update", "products.delete",
        "productscategories.read", "productscategories.create", "productscategories.update", "productscategories.delete",
        "productwarehouses.read", "productwarehouses.create", "productwarehouses.update", "productwarehouses.delete",
        "productwallets.read", "productwallets.create", "productwallets.update", "productwallets.delete",
        "productstockinitials.read", "productstockinitials.create", "productstockinitials.update", "productstockinitials.delete",
        "clients.read", "clients.create", "clients.update", "clients.delete",
        "sales.read", "sales.create", "sales.update", "sales.delete",
        "salepayments.read", "salepayments.create", "salepayments.update", "salepayments.delete",
        "saledetails.read", "saledetails.create", "saledetails.update", "saledetails.delete",
        "saledetailattentions.read", "saledetailattentions.create", "saledetailattentions.update", "saledetailattentions.delete",
        "refundproducts.read", "refundproducts.create", "refundproducts.update", "refundproducts.delete",
        "suppliers.read", "suppliers.create", "suppliers.update", "suppliers.delete",
        "purchases.read", "purchases.create", "purchases.update", "purchases.delete",
        "purchasedetails.read", "purchasedetails.create", "purchasedetails.update", "purchasedetails.delete",
        "transports.read", "transports.create", "transports.update", "transports.delete",
        "conversions.read", "conversions.create", "conversions.update", "conversions.delete",
        "productbatches.read", "productbatches.create", "productbatches.update", "productbatches.delete",
        "salebatchusages.read", "salebatchusages.create", "salebatchusages.update", "salebatchusages.delete",
        "productmasters.read", "productmasters.create", "productmasters.update", "productmasters.delete",
        "productbrands.read", "productbrands.create", "productbrands.update", "productbrands.delete",
        "ingredients.read", "ingredients.create", "ingredients.update", "ingredients.delete",
    ]]
    role.permissions.extend(perms)

    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role
