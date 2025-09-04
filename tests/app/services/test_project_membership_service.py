from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.project_membership_service import ProjectMembershipService
from app.schemas.project_membership import (
    ProjectMembershipCreate,
    ProjectMembershipUpdate,
)
from app.constants.membership import ProjectMembershipRoles


def test_create_project_membership(db: Session, setup_user, setup_project):
    service = ProjectMembershipService(db)
    membership_in = ProjectMembershipCreate(
        user_id=setup_user.id,
        project_id=setup_project.id,
        role=ProjectMembershipRoles.COLLABORATOR,
        created_by_id=setup_user.id,
    )
    membership = service.create_project_membership(membership_in)

    assert membership.id is not None
    assert membership.user_id == setup_user.id
    assert membership.project_id == setup_project.id
    assert membership.role == ProjectMembershipRoles.COLLABORATOR


def test_get_project_membership(db: Session, setup_project_membership):
    service = ProjectMembershipService(db)
    m = setup_project_membership
    retrieved = service.get_project_membership(m.id)
    assert retrieved is not None
    assert retrieved.id == m.id
    assert retrieved.user_id == m.user_id


def test_update_project_membership(db: Session, setup_project_membership):
    service = ProjectMembershipService(db)
    m = setup_project_membership

    updated = service.update_project_membership(
        m.id, ProjectMembershipUpdate(role=ProjectMembershipRoles.ADMIN)
    )
    assert updated is not None
    assert updated.role == ProjectMembershipRoles.ADMIN


def test_delete_project_membership(db: Session, setup_project_membership):
    service = ProjectMembershipService(db)
    m = setup_project_membership

    ok = service.delete_project_membership(m.id)
    assert ok is True
    assert service.get_project_membership(m.id) is None


def test_search_project_memberships(db: Session, setup_project_membership):
    service = ProjectMembershipService(db)
    m = setup_project_membership

    results = service.search({"project_id": m.project_id})
    assert len(results) >= 1

    results = service.search({"role": {"operator": "in", "value": [m.role]}})
    assert len(results) >= 1
