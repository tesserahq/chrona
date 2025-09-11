from app.commands.workspaces.create_workspace_command import CreateWorkspaceCommand
from app.commands.projects.create_project_command import CreateProjectCommand
from app.schemas.project import ProjectCreate, Project
from app.utils.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceStats,
)
from app.services.workspace_service import WorkspaceService
from app.schemas.common import ListResponse
from app.routers.utils.dependencies import get_workspace_by_id
from app.exceptions.workspace_exceptions import WorkspaceLockedError

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=ListResponse[Workspace])
def list_workspaces(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    workspaces = WorkspaceService(db).get_workspaces_by_user_memberships(
        current_user.id, skip, limit
    )
    return ListResponse(data=workspaces)


@router.post("", response_model=Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    workspace.created_by_id = current_user.id

    return CreateWorkspaceCommand(db).execute(workspace_create=workspace)


@router.get("/{workspace_id}", response_model=Workspace)
def get_workspace(workspace: Workspace = Depends(get_workspace_by_id)):
    return workspace


@router.put("/{workspace_id}", response_model=Workspace)
def update_workspace(
    workspace_update: WorkspaceUpdate,
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
):
    updated_workspace = WorkspaceService(db).update_workspace(
        workspace.id, workspace_update
    )

    return updated_workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
):
    try:
        success = WorkspaceService(db).delete_workspace(workspace.id)
        if not success:
            raise HTTPException(status_code=404, detail="Workspace not found")
    except WorkspaceLockedError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/{workspace_id}/stats", response_model=WorkspaceStats)
def get_workspace_stats(
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get comprehensive statistics for a workspace."""
    service = WorkspaceService(db)
    stats = service.get_workspace_stats_for_user(workspace.id, current_user.id)

    if not stats:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return stats


@router.get("/{workspace_id}/projects", response_model=ListResponse[Project])
def list_projects(
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List projects in a workspace."""
    from app.services.membership_service import MembershipService

    membership_service = MembershipService(db)
    projects = membership_service.get_accessible_projects_for_user(
        workspace.id, current_user.id
    )
    return ListResponse(data=projects)


@router.post(
    "/{workspace_id}/projects",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project: ProjectCreate,
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new project in a workspace."""
    # Override the workspace_id in the payload for safety
    project.workspace_id = workspace.id

    command = CreateProjectCommand(db)
    return command.execute(project, current_user.id)
