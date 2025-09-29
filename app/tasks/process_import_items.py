from uuid import UUID

from app.db import SessionLocal
from app.core.celery_app import celery_app
from app.commands.projects.process_import_request_command import (
    ProcessImportRequestCommand,
)
from app.services.import_request_service import ImportRequestService
from app.core.logging_config import get_logger


@celery_app.task
def process_import_items(import_request_id: str) -> None:
    """
    Process import items for a given import request.
    This is an async task that runs in the background.
    """
    # Debug: Print to stdout to ensure we can see something
    print(f"DEBUG: Task started for import request {import_request_id}")

    logger = get_logger("chrona.tasks.process_import_items")
    print(f"DEBUG: Logger created: {logger}")
    print(f"DEBUG: Logger level: {logger.level}")
    print(f"DEBUG: Logger handlers: {logger.handlers}")
    print(f"DEBUG: Logger propagate: {logger.propagate}")

    logger.info(f"Processing import items for import request {import_request_id}")
    print(f"DEBUG: Logger.info called")
    db = SessionLocal()
    try:
        try:
            logger.info(f"Getting import request {import_request_id}")
            # Convert string ID to UUID
            request_id = UUID(import_request_id)

            # Get import request to find associated project
            import_request_service = ImportRequestService(db)
            import_request = import_request_service.get_import_request(request_id)

            if not import_request:
                raise RuntimeError(f"Import request {import_request_id} not found")

            logger.info(f"Getting project {import_request.project_id}")
            # Get the project from the import request relationship
            project = import_request.project

            if not project:
                raise RuntimeError(f"Project {import_request.project_id} not found")

            logger.info(f"Processing import request {import_request_id}")
            # Process the import request
            command = ProcessImportRequestCommand(db)
            command.execute(request_id, project)

        except Exception as e:
            raise RuntimeError(f"Failed to process import items: {str(e)}")
        finally:
            db.commit()
    finally:
        db.close()
