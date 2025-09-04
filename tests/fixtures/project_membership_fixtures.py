import pytest
from app.models.project_membership import ProjectMembership
from app.constants.membership import ProjectMembershipRoles


@pytest.fixture
def setup_project_membership(db, setup_user, setup_project):
    membership = ProjectMembership(
        user_id=setup_user.id,
        project_id=setup_project.id,
        role=ProjectMembershipRoles.COLLABORATOR,
        created_by_id=setup_user.id,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
