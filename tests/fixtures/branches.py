import pytest

@pytest.fixture
def test_branch(db_session):
    from pharmatrack.models.branches.orm import Branch
    branch_data = {
        "name": "Main Branch",
        "address": "123 Main St, City, Country"
    }
    branch = Branch(**branch_data)
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)
    return branch

@pytest.fixture
def another_branch(db_session):
    from pharmatrack.models.branches.orm import Branch
    branch_data = {
        "name": "Secondary Branch",
        "address": "789 Secondary St, City, Country"
    }
    branch = Branch(**branch_data)
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)
    return branch

@pytest.fixture
def test_branch_with_users(db_session, test_user_with_branch):
    from pharmatrack.models.branches.orm import Branch
    branch_data = {
        "name": "Branch with Users",
        "address": "456 Branch St, City, Country"
    }
    branch = Branch(**branch_data)
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)

    # Associate the test user with this branch
    test_user_with_branch.branch_id = branch.id
    db_session.commit()

    return branch