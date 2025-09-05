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
from app.routers.utils.dependencies import get_entry_by_id
from app.schemas.common import ListResponse

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("/search", response_model=EntrySearchResponse)
def search_entries(
    filters: EntrySearchFilters,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search entries based on provided filters.

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
    results = service.search(filters.model_dump(exclude_none=True))
    return EntrySearchResponse(data=results)


@router.get("", response_model=ListResponse[Entry])
def list_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all entries with pagination."""
    service = EntryService(db)
    entries = service.get_entries(skip, limit)
    return ListResponse(data=entries)


@router.post("", response_model=Entry, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry: EntryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new entry."""
    service = EntryService(db)
    return service.create_entry(entry)


@router.get("/{entry_id}", response_model=Entry)
def get_entry(
    entry: EntryModel = Depends(get_entry_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific entry by ID."""
    return entry


@router.put("/{entry_id}", response_model=Entry)
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


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
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
