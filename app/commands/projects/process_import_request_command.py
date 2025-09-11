from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.commands.projects.process_import_item_command import ProcessImportItemCommand
from app.services.import_request_service import ImportRequestService
from app.constants.import_constants import ImportRequestStatuses


class ProcessImportRequestCommand:
    """Command to process all items in an import request."""

    def __init__(self, db: Session):
        self.db = db
        self.import_request_service = ImportRequestService(db)
        self.process_item_command = ProcessImportItemCommand(db)

    def execute(
        self,
        import_request_id: UUID,
        project: Project,
    ) -> Dict[str, Any]:
        """
        Process all items in an import request.

        :param import_request_id: The import request ID to process
        :param project: The project to create entities in
        :return: Dictionary with processing results
        """
        # Get the import request
        import_request = self.import_request_service.get_import_request(
            import_request_id
        )
        if not import_request:
            return {
                "success": False,
                "error": f"Import request {import_request_id} not found",
            }

        # Get all items for this import request
        items = self.import_request_service.get_import_request_items(import_request_id)

        if not items:
            return {
                "success": False,
                "error": f"No items found for import request {import_request_id}",
            }

        # Update import request status to processing
        from app.schemas.import_request import ImportRequestUpdate

        self.import_request_service.update_import_request(
            import_request_id,
            ImportRequestUpdate(status=ImportRequestStatuses.PROCESSING),
        )

        # Process each item
        success_count = 0
        failure_count = 0
        processed_items = []
        errors = []

        for item in items:
            try:
                result = self.process_item_command.execute(item, project)
                processed_items.append(
                    {
                        "item_id": str(item.id),
                        "success": result["success"],
                        "author_id": result.get("author_id"),
                        "entry_id": result.get("entry_id"),
                        "comment_ids": result.get("comment_ids", []),
                        "source_author_id": result.get("source_author_id"),
                        "error": result.get("error"),
                    }
                )

                if result["success"]:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(
                        f"Item {item.id}: {result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                failure_count += 1
                error_msg = f"Item {item.id}: {str(e)}"
                errors.append(error_msg)
                processed_items.append(
                    {
                        "item_id": str(item.id),
                        "success": False,
                        "error": str(e),
                    }
                )

        # Update import request with final status
        final_status = (
            ImportRequestStatuses.COMPLETED
            if failure_count == 0
            else ImportRequestStatuses.COMPLETED_WITH_ERRORS
        )

        self.import_request_service.update_import_request(
            import_request_id,
            ImportRequestUpdate(
                status=final_status,
                success_count=success_count,
                failure_count=failure_count,
            ),
        )

        return {
            "success": True,
            "import_request_id": import_request_id,
            "total_items": len(items),
            "processed_items": len(processed_items),
            "success_count": success_count,
            "failure_count": failure_count,
            "status": final_status,
            "processed_items": processed_items,
            "errors": errors,
        }

    def execute_batch(
        self,
        import_request_ids: List[UUID],
        project: Project,
    ) -> Dict[str, Any]:
        """
        Process multiple import requests in batch.

        :param import_request_ids: List of import request IDs to process
        :param project: The project to create entities in
        :return: Dictionary with batch processing results
        """
        results = []
        total_success = 0
        total_failure = 0
        total_items = 0

        for import_request_id in import_request_ids:
            result = self.execute(import_request_id, project)
            results.append(
                {
                    "import_request_id": import_request_id,
                    "result": result,
                }
            )

            if result["success"]:
                total_success += result["success_count"]
                total_failure += result["failure_count"]
                total_items += result["total_items"]

        return {
            "success": True,
            "total_import_requests": len(import_request_ids),
            "total_items": total_items,
            "total_success": total_success,
            "total_failure": total_failure,
            "results": results,
        }
