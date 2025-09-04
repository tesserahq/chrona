from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.services.invitation_service import InvitationService
from app.services.membership_service import MembershipService
from app.services.workspace_service import WorkspaceService
from app.models.workspace import Workspace
from app.services.project_service import ProjectService
from app.models.project import Project
from app.models.project_membership import ProjectMembership
from app.services.project_membership_service import ProjectMembershipService


def get_workspace_by_id(
    workspace_id: UUID,
    db: Session = Depends(get_db),
) -> Workspace:
    """FastAPI dependency to get a workspace by ID.

    Args:
        workspace_id: The UUID of the workspace to retrieve
        db: Database session dependency

    Returns:
        Workspace: The retrieved workspace

    Raises:
        HTTPException: If the workspace is not found
    """
    workspace = WorkspaceService(db).get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


def get_project_by_id(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> Project:
    """FastAPI dependency to get a project by ID.

    Args:
        project_id: The UUID of the project to retrieve
        db: Database session dependency

    Returns:
        Project: The retrieved project

    Raises:
        HTTPException: If the project is not found
    """
    project = ProjectService(db).get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def get_access_token(
    authorization: str = Header(..., description="Authorization header"),
) -> str:
    """FastAPI dependency to get the access token from the authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization header format"
        )
    return authorization[7:]  # Remove "Bearer " prefix


def get_invitation_by_id(
    invitation_id: UUID,
    db: Session = Depends(get_db),
) -> Invitation:
    """FastAPI dependency to get an invitation by ID.

    Args:
        invitation_id: The UUID of the invitation to retrieve
        db: Database session dependency

    Returns:
        Invitation: The retrieved invitation

    Raises:
        HTTPException: If the invitation is not found
    """
    invitation = InvitationService(db).get_invitation(invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation


def get_membership_by_id(
    membership_id: UUID,
    db: Session = Depends(get_db),
) -> Membership:
    """FastAPI dependency to get a membership by ID.

    Args:
        membership_id: The UUID of the membership to retrieve
        db: Database session dependency

    Returns:
        Membership: The retrieved membership

    Raises:
        HTTPException: If the membership is not found
    """
    membership = MembershipService(db).get_membership(membership_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    return membership


def get_project_membership_by_id(
    membership_id: UUID,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db),
) -> ProjectMembership:
    """FastAPI dependency to get a project membership by ID, scoped to a project."""
    pm = ProjectMembershipService(db).get_project_membership(membership_id)
    if pm is None or pm.project_id != project.id:
        raise HTTPException(status_code=404, detail="Project membership not found")
    return pm
