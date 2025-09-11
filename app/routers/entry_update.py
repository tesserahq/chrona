from app.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.entry_update import (
    EntryUpdateCreate,
    EntryUpdateUpdate,
    EntryUpdate,
)
from app.services.entry_update_service import EntryUpdateService
from app.models.entry_update import EntryUpdate as EntryUpdateModel
from app.models.entry import Entry as EntryModel
from app.routers.utils.dependencies import get_entry_update_by_id, get_entry_by_id
from app.schemas.common import ListResponse

router = APIRouter(prefix="/entries/{entry_id}/entry-updates", tags=["entry-updates"])
standalone_router = APIRouter(prefix="/entry-updates", tags=["entry-updates"])


@router.get("", response_model=ListResponse[EntryUpdate])
def list_entry_updates(
    entry: EntryModel = Depends(get_entry_by_id),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all entry updates for a specific entry with pagination."""
    service = EntryUpdateService(db)
    # Filter entry updates by entry_id
    entry_updates = service.search({"entry_id": entry.id})
    # Apply pagination manually since we're using search
    entry_updates = entry_updates[skip : skip + limit]
    return ListResponse(data=entry_updates)


@router.post("", response_model=EntryUpdate, status_code=status.HTTP_201_CREATED)
def create_entry_update(
    entry_update: EntryUpdateCreate,
    entry: EntryModel = Depends(get_entry_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new entry update for a specific entry."""
    service = EntryUpdateService(db)
    # Ensure the entry update belongs to the specified entry
    entry_update.entry_id = entry.id
    return service.create_entry_update(entry_update)


@standalone_router.get("/{entry_update_id}", response_model=EntryUpdate)
def get_entry_update(
    entry_update: EntryUpdateModel = Depends(get_entry_update_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific entry update by ID."""
    return entry_update


@standalone_router.put("/{entry_update_id}", response_model=EntryUpdate)
def update_entry_update(
    entry_update_update: EntryUpdateUpdate,
    entry_update: EntryUpdateModel = Depends(get_entry_update_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing entry update."""
    service = EntryUpdateService(db)
    updated = service.update_entry_update(entry_update.id, entry_update_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Entry update not found")
    return updated


@standalone_router.delete("/{entry_update_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry_update(
    entry_update: EntryUpdateModel = Depends(get_entry_update_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an entry update."""
    service = EntryUpdateService(db)
    success = service.delete_entry_update(entry_update.id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry update not found")
    return {"message": "Entry update deleted successfully"}
