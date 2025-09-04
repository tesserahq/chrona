import pytest
from app.models.membership import Membership
from app.constants.membership import COLLABORATOR_ROLE


@pytest.fixture
def setup_membership(db, setup_user, setup_workspace):
    """Create a test membership for use in tests."""
    user = setup_user
    workspace = setup_workspace

    membership_data = {
        "user_id": user.id,
        "workspace_id": workspace.id,
        "role": COLLABORATOR_ROLE,
        "created_by_id": workspace.created_by_id,
    }

    membership = Membership(**membership_data)
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return membership


@pytest.fixture
def setup_different_membership(db, setup_another_user, setup_different_workspace):
    """Create a test membership for the different user in the different workspace."""
    user = setup_another_user
    workspace = setup_different_workspace

    membership_data = {
        "user_id": user.id,
        "workspace_id": workspace.id,
        "role": COLLABORATOR_ROLE,
        "created_by_id": workspace.created_by_id,
    }

    membership = Membership(**membership_data)
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return membership


@pytest.fixture
def setup_another_user_membership(db, setup_another_user, setup_workspace, faker):
    """Create a membership for another user in the same account."""
    membership_data = {
        "user_id": setup_another_user.id,
        "workspace_id": setup_workspace.id,
        "role": COLLABORATOR_ROLE,
        "created_by_id": setup_another_user.id,
    }

    membership = Membership(**membership_data)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@pytest.fixture
def setup_different_workspace_membership(
    db, setup_user, setup_different_workspace, faker
):
    """Create a membership for a user in a different account."""
    membership_data = {
        "user_id": setup_user.id,
        "workspace_id": setup_different_workspace.id,
        "role": COLLABORATOR_ROLE,
        "created_by_id": setup_user.id,
    }

    membership = Membership(**membership_data)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
