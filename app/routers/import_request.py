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
from app.schemas.import_request import (
    ImportRequestProcessResponse,
    ImportRequest,
    ImportRequestSearchFilters,
)
from app.commands.projects.process_import_request_command import (
    ProcessImportRequestCommand,
)
from app.models.import_request import ImportRequest as ImportRequestModel
from app.models.project import Project as ProjectModel
from app.services.import_request_service import ImportRequestService
from app.routers.utils.dependencies import get_project_by_id, get_import_request_by_id

router = APIRouter(prefix="/import-requests", tags=["import-requests"])


@router.get(
    "/projects/{project_id}/import-requests", response_model=Page[ImportRequest]
)
def list_import_requests(
    project_id: UUID,
    project: ProjectModel = Depends(get_project_by_id),
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all import requests for a specific project with pagination."""
    service = ImportRequestService(db)
    query = service.get_import_requests_by_project_query(project_id)
    return paginate(query, params)


@router.post(
    "/projects/{project_id}/import-requests/search", response_model=Page[ImportRequest]
)
def search_import_requests(
    project_id: UUID,
    filters: ImportRequestSearchFilters,
    project: ProjectModel = Depends(get_project_by_id),
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search import requests within a specific project based on provided filters.

    Each filter field can be either:
    - A direct value (e.g., "status": "pending")
    - A search operator object with:
        - operator: One of "=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"
        - value: The value to compare against

    Example:
    {
        "status": {"operator": "ilike", "value": "%pending%"},
        "project_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    """
    service = ImportRequestService(db)
    # Add project_id to filters to scope the search
    search_filters = filters.model_dump(exclude_none=True)
    search_filters["project_id"] = str(project_id)
    query = service.search_query(search_filters)
    return paginate(query, params)


@router.post(
    "/{import_request_id}/process", response_model=ImportRequestProcessResponse
)
def process_import_request(
    import_request: ImportRequestModel = Depends(get_import_request_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ImportRequestProcessResponse:
    """
    Process an import request.

    This endpoint processes all items in the specified import request,
    creating entries, authors, and entry_updates in the associated project.
    """

    # Get the project associated with this import request
    project = (
        db.query(ProjectModel)
        .filter(ProjectModel.id == import_request.project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found for this import request",
        )

    # Execute the process command
    command = ProcessImportRequestCommand(db)
    result = command.execute(import_request.id, project)

    return ImportRequestProcessResponse(**result)
