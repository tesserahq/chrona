from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.models.author import Author
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.services.author_service import AuthorService
from app.services.invitation_service import InvitationService
from app.services.membership_service import MembershipService
from app.services.workspace_service import WorkspaceService
from app.models.workspace import Workspace
from app.services.project_service import ProjectService
from app.models.project import Project
from app.models.project_membership import ProjectMembership
from app.services.project_membership_service import ProjectMembershipService
from app.services.entry_service import EntryService
from app.models.entry import Entry
from app.services.comment_service import CommentService
from app.models.comment import Comment
from app.services.import_request_service import ImportRequestService
from app.models.import_request import ImportRequest
from app.services.digest_generation_config_service import DigestGenerationConfigService
from app.models.digest_generation_config import DigestGenerationConfig


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


def get_entry_by_id(
    entry_id: UUID,
    db: Session = Depends(get_db),
) -> Entry:
    """FastAPI dependency to get an entry by ID.

    Args:
        entry_id: The UUID of the entry to retrieve
        db: Database session dependency

    Returns:
        Entry: The retrieved entry

    Raises:
        HTTPException: If the entry is not found
    """
    entry = EntryService(db).get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


def get_comment_by_id(
    comment_id: UUID,
    db: Session = Depends(get_db),
) -> Comment:
    """FastAPI dependency to get a comment by ID.

    Args:
        comment_id: The UUID of the comment to retrieve
        db: Database session dependency

    Returns:
        Comment: The retrieved comment

    Raises:
        HTTPException: If the comment is not found
    """
    comment = CommentService(db).get_comment(comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def get_author_by_id(
    author_id: UUID,
    db: Session = Depends(get_db),
) -> Author:
    """FastAPI dependency to get an author by ID.

    Args:
        author_id: The UUID of the author to retrieve
        db: Database session dependency

    Returns:
        Author: The retrieved author

    Raises:
        HTTPException: If the author is not found
    """
    author = AuthorService(db).get_author(author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


def get_import_request_by_id(
    import_request_id: UUID,
    db: Session = Depends(get_db),
) -> ImportRequest:
    """FastAPI dependency to get an import request by ID.

    Args:
        import_request_id: The UUID of the import request to retrieve
        db: Database session dependency

    Returns:
        ImportRequest: The retrieved import request

    Raises:
        HTTPException: If the import request is not found
    """
    import_request = ImportRequestService(db).get_import_request(import_request_id)
    if import_request is None:
        raise HTTPException(status_code=404, detail="Import request not found")
    return import_request


def get_digest_generation_config_by_id(
    digest_generation_config_id: UUID,
    db: Session = Depends(get_db),
) -> DigestGenerationConfig:
    """FastAPI dependency to get a digest generation config by ID.

    Args:
        digest_generation_config_id: The UUID of the digest generation config to retrieve
        db: Database session dependency

    Returns:
        DigestGenerationConfig: The retrieved digest generation config

    Raises:
        HTTPException: If the digest generation config is not found
    """
    digest_generation_config = DigestGenerationConfigService(
        db
    ).get_digest_generation_config(digest_generation_config_id)
    if digest_generation_config is None:
        raise HTTPException(
            status_code=404, detail="Digest generation config not found"
        )
    return digest_generation_config
