from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.import_request import ImportRequest
from app.models.import_request_item import ImportRequestItem
from app.schemas.project_import import (
    ImportItemRequest,
    ImportItemData,
)
from app.schemas.import_request import ImportRequestCreate, ImportRequestUpdate
from app.schemas.import_request_item import ImportRequestItemCreate
from app.services.source_service import SourceService
from app.services.import_request_service import ImportRequestService
from app.constants.import_constants import (
    ImportRequestStatuses,
    ImportItemStatuses,
)


class ImportItemsCommand:
    def __init__(self, db: Session):
        self.db = db
        self.source_service = SourceService(db)
        self.import_request_service = ImportRequestService(db)

    def execute(
        self,
        project: Project,
        import_request: ImportItemRequest,
        requested_by_id: UUID,
    ) -> Dict[str, Any]:
        """
        Execute the command to import project data.

        :param project: The project to import data into
        :param import_request: The import request data
        :param requested_by_id: ID of the user requesting the import
        :return: Dictionary with import results
        """
        # Create or get the source for this import
        source_identifier = f"import_{project.id}"
        source = self.source_service.get_or_create_source_by_identifier(
            identifier=source_identifier,
            workspace_id=project.workspace_id,
            name=source_identifier.capitalize(),
        )

        # Create the import request
        import_request_data = ImportRequestCreate(
            source_id=source.id,
            requested_by_id=requested_by_id,
            status=ImportRequestStatuses.PROCESSING,
            received_count=len(import_request.items),
            success_count=0,
            failure_count=0,
            project_id=project.id,
            options={"source_type": "bulk_import"},
        )

        db_import_request = self.import_request_service.create_import_request(
            import_request_data
        )

        success_count = 0
        failure_count = 0

        # Process each item
        # TODO: We could insert all the items in a bulk insert instead of one by one
        for item_data in import_request.items:
            try:
                # Create import request item with raw payload
                import_item = self._create_import_request_item(
                    db_import_request, source, item_data, ImportItemStatuses.SUCCESS
                )

                success_count += 1

            except Exception as e:
                # Create failed import request item
                self._create_import_request_item(
                    db_import_request, source, item_data, ImportItemStatuses.FAILED
                )
                failure_count += 1
                print(
                    f"Failed to import item: {e}"
                )  # In production, use proper logging

        # Update import request with final counts
        self.import_request_service.update_import_request(
            db_import_request.id,
            ImportRequestUpdate(
                status=(
                    ImportRequestStatuses.COMPLETED
                    if failure_count == 0
                    else ImportRequestStatuses.COMPLETED_WITH_ERRORS
                ),
                success_count=success_count,
                failure_count=failure_count,
            ),
        )

        return {
            "id": str(db_import_request.id),
            "total_items": len(import_request.items),
            "processed_items": success_count + failure_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "status": (
                ImportRequestStatuses.COMPLETED
                if failure_count == 0
                else ImportRequestStatuses.COMPLETED_WITH_ERRORS
            ),
        }

    def _create_import_request_item(
        self,
        import_request: ImportRequest,
        source,
        item_data: ImportItemData,
        status: str,
    ) -> ImportRequestItem:
        """Create an import request item."""
        import_item_create = ImportRequestItemCreate(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id=item_data.author.id,  # Use the author's ID as source_item_id
            raw_payload=item_data.model_dump(),  # Store the full item data
            status=status,
        )

        return self.import_request_service.create_import_request_item(
            import_item_create
        )
