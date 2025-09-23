from tessera_sdk.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Union

from app.db import get_db
from app.schemas.digest import (
    DigestUpdate,
    Digest,
    DigestWithEntries,
)
from app.services.digest_service import DigestService
from app.models.digest import Digest as DigestModel
from app.routers.utils.dependencies import get_digest_by_id

# Individual digest endpoints
router = APIRouter(prefix="/digests", tags=["digests"])


@router.get("/{digest_id}", response_model=Union[Digest, DigestWithEntries])
def get_digest(
    digest_id: UUID,
    include: str = Query(
        None,
        description="Include related resources. Use 'entries' to include entries with their entry_updates",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific digest by ID."""
    service = DigestService(db)

    if include == "entries":
        digest = service.get_digest_with_entries(digest_id)
        if not digest:
            raise HTTPException(status_code=404, detail="Digest not found")
        return digest
    else:
        digest = service.get_digest(digest_id)
        if not digest:
            raise HTTPException(status_code=404, detail="Digest not found")
        return digest


@router.put("/{digest_id}", response_model=Digest)
def update_digest(
    digest_id: UUID,
    digest_update: DigestUpdate,
    digest: DigestModel = Depends(get_digest_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a digest."""
    service = DigestService(db)
    updated = service.update_digest(digest_id, digest_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Digest not found")
    return updated


@router.delete("/{digest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_digest(
    digest_id: UUID,
    digest: DigestModel = Depends(get_digest_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a digest (soft delete)."""
    service = DigestService(db)
    success = service.delete_digest(digest_id)
    if not success:
        raise HTTPException(status_code=404, detail="Digest not found")
