from app.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.schemas.import_request import ImportRequestProcessResponse
from app.commands.projects.process_import_request_command import (
    ProcessImportRequestCommand,
)
from app.models.import_request import ImportRequest as ImportRequestModel
from app.models.project import Project as ProjectModel
from app.routers.utils.dependencies import get_project_by_id, get_import_request_by_id

router = APIRouter(prefix="/import-requests", tags=["import-requests"])


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
    creating entries, authors, and comments in the associated project.
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
