from app.utils.auth import get_current_user
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
from app.schemas.digest_generation_config import (
    DigestGenerationConfigCreate,
    DigestGenerationConfigUpdate,
    DigestGenerationConfig,
    DigestGenerationConfigSearchFilters,
)
from app.services.digest_generation_config_service import DigestGenerationConfigService
from app.models.digest_generation_config import (
    DigestGenerationConfig as DigestGenerationConfigModel,
)
from app.models.project import Project as ProjectModel
from app.routers.utils.dependencies import (
    get_project_by_id,
    get_digest_generation_config_by_id,
)


# Project-scoped router for list and create operations
project_router = APIRouter(
    prefix="/projects/{project_id}/digest-generation-configs",
    tags=["digest-generation-configs"],
)

# Global router for individual digest generation config operations
router = APIRouter(
    prefix="/digest-generation-configs", tags=["digest-generation-configs"]
)


# Project-scoped endpoints
@project_router.get("", response_model=Page[DigestGenerationConfig])
def list_digest_generation_configs(
    project: ProjectModel = Depends(get_project_by_id),
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all digest generation configs in a project with pagination."""
    service = DigestGenerationConfigService(db)
    query = service.get_digest_generation_configs_by_project_query(project.id)
    return paginate(query, params)


@project_router.post("/search", response_model=Page[DigestGenerationConfig])
def search_digest_generation_configs(
    project_id: UUID,
    filters: DigestGenerationConfigSearchFilters,
    project: ProjectModel = Depends(get_project_by_id),
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search digest generation configs within a specific project based on provided filters.

    Each filter field can be either:
    - A direct value (e.g., "title": "My Config")
    - A search operator object with:
        - operator: One of "=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"
        - value: The value to compare against

    Example:
    {
        "title": {"operator": "ilike", "value": "%daily%"},
        "project_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    """
    service = DigestGenerationConfigService(db)
    # Add project_id to filters to scope the search
    search_filters = filters.model_dump(exclude_none=True)
    search_filters["project_id"] = str(project_id)
    query = service.search_digest_generation_configs_query(search_filters)
    return paginate(query, params)


@project_router.post(
    "", response_model=DigestGenerationConfig, status_code=status.HTTP_201_CREATED
)
def create_digest_generation_config(
    digest_generation_config: DigestGenerationConfigCreate,
    project: ProjectModel = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new digest generation config in a project."""
    service = DigestGenerationConfigService(db)
    return service.create_digest_generation_config(digest_generation_config, project.id)


# Global endpoints for individual digest generation config operations
@router.get("/{digest_generation_config_id}", response_model=DigestGenerationConfig)
def get_digest_generation_config(
    digest_generation_config: DigestGenerationConfigModel = Depends(
        get_digest_generation_config_by_id
    ),
    current_user=Depends(get_current_user),
):
    """Get a specific digest generation config by ID."""
    return digest_generation_config


@router.put("/{digest_generation_config_id}", response_model=DigestGenerationConfig)
def update_digest_generation_config(
    digest_generation_config_update: DigestGenerationConfigUpdate,
    digest_generation_config: DigestGenerationConfigModel = Depends(
        get_digest_generation_config_by_id
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a digest generation config."""
    service = DigestGenerationConfigService(db)
    updated_digest_generation_config = service.update_digest_generation_config(
        digest_generation_config.id, digest_generation_config_update
    )
    if not updated_digest_generation_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digest generation config not found",
        )
    return updated_digest_generation_config


@router.delete("/{digest_generation_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_digest_generation_config(
    digest_generation_config: DigestGenerationConfigModel = Depends(
        get_digest_generation_config_by_id
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a digest generation config."""
    service = DigestGenerationConfigService(db)
    success = service.delete_digest_generation_config(digest_generation_config.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digest generation config not found",
        )
