from app.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db import get_db
from app.schemas.project import (
    ProjectUpdate,
    Project,
    ProjectSearchFilters,
    ProjectSearchResponse,
)
from app.services.project_service import ProjectService
from app.models.project import Project as ProjectModel
from app.routers.utils.dependencies import (
    get_project_by_id,
    get_project_membership_by_id,
)
from app.services.project_membership_service import ProjectMembershipService
from app.schemas.project_membership import (
    ProjectMembershipUpdate,
    ProjectMembershipInDB,
    ProjectMembershipResponse,
)
from app.schemas.common import ListResponse
from app.models.project_membership import ProjectMembership
from app.schemas.project_import import ImportItemRequest, ImportItemResponse
from app.commands.projects.import_items_command import ImportItemsCommand

router = APIRouter(prefix="/projects", tags=["workspace-projects"])


@router.post("/search", response_model=ProjectSearchResponse)
def search_projects(
    filters: ProjectSearchFilters,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search projects based on provided filters.

    Each filter field can be either:
    - A direct value (e.g., "name": "Project 1")
    - A search operator object with:
        - operator: One of "=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"
        - value: The value to compare against

    Example:
    {
        "name": {"operator": "ilike", "value": "%test%"},
        "workspace_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    """
    service = ProjectService(db)
    results = service.search(filters.model_dump(exclude_none=True))
    return ProjectSearchResponse(data=results)


@router.get(
    "/{project_id}/memberships", response_model=ListResponse[ProjectMembershipResponse]
)
def list_project_memberships(
    project: ProjectModel = Depends(get_project_by_id),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProjectMembershipService(db)
    memberships = service.get_memberships_by_project(UUID(str(project.id)), skip, limit)
    return ListResponse(data=memberships)


@router.get("/{project_id}", response_model=Project)
def get_project(
    project: ProjectModel = Depends(get_project_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific project by ID."""
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_update: ProjectUpdate,
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing project."""
    service = ProjectService(db)
    updated = service.update_project(UUID(str(project.id)), project_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.put(
    "/{project_id}/memberships/{membership_id}",
    response_model=ProjectMembershipInDB,
)
def update_project_membership(
    membership_update: ProjectMembershipUpdate,
    membership: ProjectMembership = Depends(get_project_membership_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProjectMembershipService(db)
    updated = service.update_project_membership(
        UUID(str(membership.id)), membership_update
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Project membership not found")
    return updated


@router.get(
    "/{project_id}/memberships/{membership_id}",
    response_model=ProjectMembershipResponse,
)
def get_project_membership(
    membership: ProjectMembership = Depends(get_project_membership_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProjectMembershipService(db)
    db_membership = service.get_project_membership(UUID(str(membership.id)))
    if db_membership is None:
        raise HTTPException(status_code=404, detail="Project membership not found")
    return db_membership


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a project."""
    service = ProjectService(db)
    success = service.delete_project(UUID(str(project.id)))
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}


@router.delete(
    "/{project_id}/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project_membership(
    membership: ProjectMembership = Depends(get_project_membership_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProjectMembershipService(db)
    success = service.delete_project_membership(UUID(str(membership.id)))
    if not success:
        raise HTTPException(status_code=404, detail="Project membership not found")


@router.post("/{project_id}/import", response_model=ImportItemResponse)
def import_items(
    import_request: ImportItemRequest,
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Import data into a project.

    This endpoint accepts a list of items with their associated authors and creates
    entries, authors, and import request records in the database.
    """
    command = ImportItemsCommand(db)
    result = command.execute(project, import_request, current_user.id)
    return ImportItemResponse(**result)
