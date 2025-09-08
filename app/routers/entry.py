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
from app.schemas.entry import (
    EntryCreate,
    EntryUpdate,
    Entry,
    EntrySearchFilters,
    EntrySearchResponse,
)
from app.services.entry_service import EntryService
from app.models.entry import Entry as EntryModel
from app.models.project import Project as ProjectModel
from app.routers.utils.dependencies import get_entry_by_id, get_project_by_id
from app.schemas.common import ListResponse

# Project-scoped entries router
project_entries_router = APIRouter(prefix="/projects", tags=["project-entries"])

# Individual entries router
entries_router = APIRouter(prefix="/entries", tags=["entries"])


@project_entries_router.post(
    "/{project_id}/entries/search", response_model=EntrySearchResponse
)
def search_entries(
    project_id: UUID,
    filters: EntrySearchFilters,
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search entries within a specific project based on provided filters.

    Each filter field can be either:
    - A direct value (e.g., "title": "My Entry")
    - A search operator object with:
        - operator: One of "=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"
        - value: The value to compare against

    Example:
    {
        "title": {"operator": "ilike", "value": "%test%"},
        "author_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    """
    service = EntryService(db)
    # Add project_id to filters to scope the search
    search_filters = filters.model_dump(exclude_none=True)
    search_filters["project_id"] = str(project_id)
    results = service.search(search_filters)
    return EntrySearchResponse(data=results)


@project_entries_router.get("/{project_id}/entries", response_model=ListResponse[Entry])
def list_entries(
    project_id: UUID,
    project: ProjectModel = Depends(get_project_by_id),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all entries within a specific project with pagination."""
    service = EntryService(db)
    entries = service.get_entries_by_project(project_id, skip, limit)
    return ListResponse(data=entries)


@project_entries_router.post(
    "/{project_id}/entries", response_model=Entry, status_code=status.HTTP_201_CREATED
)
def create_entry(
    project_id: UUID,
    entry: EntryCreate,
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new entry within a specific project."""
    service = EntryService(db)
    # Ensure the entry is created for the specified project
    entry_data = entry.model_dump()
    entry_data["project_id"] = project_id
    return service.create_entry(EntryCreate(**entry_data))


# Individual entry endpoints
@entries_router.get("/{entry_id}", response_model=Entry)
def get_entry(
    entry: EntryModel = Depends(get_entry_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific entry by ID."""
    return entry


@entries_router.put("/{entry_id}", response_model=Entry)
def update_entry(
    entry_update: EntryUpdate,
    entry: EntryModel = Depends(get_entry_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing entry."""
    service = EntryService(db)
    updated = service.update_entry(entry.id, entry_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return updated


@entries_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry: EntryModel = Depends(get_entry_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an entry."""
    service = EntryService(db)
    success = service.delete_entry(entry.id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted successfully"}
