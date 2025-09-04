import pytest
from app.constants.membership import MembershipRoles
from app.models.membership import Membership
from app.models.workspace import Workspace


@pytest.fixture
def setup_workspace(db, setup_user, faker):
    """Create a test workspace in the database with optional overrides."""

    user = setup_user

    workspace_data = {
        "name": faker.name(),
        "description": faker.text(100),
        "created_by_id": user.id,
    }

    workspace = Workspace(**workspace_data)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    membership = Membership(
        user_id=user.id,
        workspace_id=workspace.id,
        role=MembershipRoles.OWNER,
        created_by_id=user.id,
    )
    db.add(membership)
    db.commit()
    return workspace


@pytest.fixture
def setup_different_workspace(db, setup_another_user, faker):
    """Create a different test workspace in the database."""
    user = setup_another_user

    workspace_data = {
        "name": faker.name(),
        "description": faker.text(100),
        "created_by_id": user.id,
    }

    workspace = Workspace(**workspace_data)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace
