from tessera_sdk.utils.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.schemas.source import SourceCreate, SourceUpdate, Source as SourceSchema
from app.schemas.common import ListResponse
from app.services.source_service import SourceService
from app.models.source import Source as SourceModel
from app.models.workspace import Workspace
from app.routers.utils.dependencies import get_workspace_by_id, get_source_by_id

# Workspace-scoped sources router
workspace_router = APIRouter(prefix="/workspaces", tags=["workspace-sources"])

# Individual sources router
router = APIRouter(prefix="/sources", tags=["sources"])


@workspace_router.get(
    "/{workspace_id}/sources", response_model=ListResponse[SourceSchema]
)
def list_sources(
    workspace_id: UUID,
    workspace: Workspace = Depends(get_workspace_by_id),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all sources within a specific workspace."""
    service = SourceService(db)
    sources = service.get_sources_by_workspace(workspace.id, skip, limit)
    return ListResponse(data=sources)


@workspace_router.post(
    "/{workspace_id}/sources",
    response_model=SourceSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    workspace_id: UUID,
    source: SourceCreate,
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new source within a specific workspace."""
    service = SourceService(db)
    return service.create_source(source, workspace.id)


# Individual source endpoints
@router.get("/{source_id}", response_model=SourceSchema)
def get_source(
    source: SourceModel = Depends(get_source_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific source by ID."""
    return source


@router.put("/{source_id}", response_model=SourceSchema)
def update_source(
    source_update: SourceUpdate,
    source: SourceModel = Depends(get_source_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing source."""
    service = SourceService(db)
    updated = service.update_source(source.id, source_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return updated


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source: SourceModel = Depends(get_source_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a source (soft delete)."""
    service = SourceService(db)
    success = service.delete_source(source.id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"message": "Source deleted successfully"}
