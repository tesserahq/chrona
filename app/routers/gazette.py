from tessera_sdk.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.db import get_db
from app.schemas.gazette import (
    GazetteCreate,
    GazetteUpdate,
    Gazette,
    GazetteShare,
    GazetteWithSectionsAndDigests,
)
from app.services.gazette_service import GazetteService
from app.commands.gazette.get_gazette_with_digests_command import (
    GetGazetteWithDigestsCommand,
)
from app.models.gazette import Gazette as GazetteModel
from app.models.project import Project as ProjectModel
from app.routers.utils.dependencies import get_project_by_id, get_gazette_by_id

# Project-scoped router for list and create operations
project_router = APIRouter(prefix="/projects/{project_id}/gazettes", tags=["gazettes"])

# Global router for individual gazette operations
router = APIRouter(prefix="/gazettes", tags=["gazettes"])


# Project-scoped endpoints
@project_router.get("", response_model=Page[Gazette])
def list_gazettes(
    project: ProjectModel = Depends(get_project_by_id),
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all gazettes in a project with pagination."""
    service = GazetteService(db)
    query = service.get_gazettes_by_project_query(project.id)
    return paginate(query, params)


@project_router.post("", response_model=Gazette, status_code=status.HTTP_201_CREATED)
def create_gazette(
    gazette_data: GazetteCreate,
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new gazette in a project."""
    service = GazetteService(db)

    # Override project_id from URL (don't trust request body)
    gazette_data.project_id = project.id

    return service.create_gazette(gazette_data)


# Global individual gazette endpoints
@router.get("/{gazette_id}", response_model=Gazette)
def get_gazette(
    gazette: GazetteModel = Depends(get_gazette_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific gazette by ID."""
    return gazette


@router.put("/{gazette_id}", response_model=Gazette)
def update_gazette(
    gazette_id: UUID,
    gazette_update: GazetteUpdate,
    gazette: GazetteModel = Depends(get_gazette_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a gazette."""
    service = GazetteService(db)
    updated = service.update_gazette(gazette_id, gazette_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Gazette not found")
    return updated


@router.delete("/{gazette_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gazette(
    gazette_id: UUID,
    gazette: GazetteModel = Depends(get_gazette_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a gazette (soft delete)."""
    service = GazetteService(db)
    success = service.delete_gazette(gazette_id)
    if not success:
        raise HTTPException(status_code=404, detail="Gazette not found")


# Share endpoints
@router.post("/{gazette_id}/share", response_model=GazetteShare)
def generate_gazette_share_key(
    gazette_id: UUID,
    gazette: GazetteModel = Depends(get_gazette_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate or get share key for a gazette."""
    service = GazetteService(db)
    gazette_with_share_key = service.generate_or_get_share_key(gazette_id)
    return gazette_with_share_key


@router.post("/{gazette_id}/regenerate-share-key", response_model=Gazette)
def regenerate_gazette_share_key(
    gazette_id: UUID,
    gazette: GazetteModel = Depends(get_gazette_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Regenerate share key for a gazette (returns gazette without exposing the new key)."""
    service = GazetteService(db)
    updated_gazette = service.regenerate_share_key(gazette_id)
    return updated_gazette


@router.get("/share/{share_key}", response_model=GazetteWithSectionsAndDigests)
def get_gazette_by_share_key(
    share_key: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a gazette by its share key along with matching published digests."""
    command = GetGazetteWithDigestsCommand(db)
    return command.execute(share_key)
