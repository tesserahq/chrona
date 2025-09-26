from uuid import UUID

from app.db import SessionLocal
from app.core.celery_app import celery_app
from app.commands.projects.process_import_request_command import (
    ProcessImportRequestCommand,
)
from app.services.import_request_service import ImportRequestService


@celery_app.task
def process_import_items(import_request_id: str) -> None:
    """
    Process import items for a given import request.
    This is an async task that runs in the background.
    """
    db = SessionLocal()
    try:
        try:
            # Convert string ID to UUID
            request_id = UUID(import_request_id)

            # Get import request to find associated project
            import_request_service = ImportRequestService(db)
            import_request = import_request_service.get_import_request(request_id)

            if not import_request:
                raise RuntimeError(f"Import request {import_request_id} not found")

            # Get the project from the import request relationship
            project = import_request.project

            if not project:
                raise RuntimeError(f"Project {import_request.project_id} not found")

            # Process the import request
            command = ProcessImportRequestCommand(db)
            command.execute(request_id, project)

        except Exception as e:
            raise RuntimeError(f"Failed to process import items: {str(e)}")
        finally:
            db.commit()
    finally:
        db.close()
