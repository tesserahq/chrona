import pytest
from uuid import uuid4

from app.commands.projects.process_import_request_command import (
    ProcessImportRequestCommand,
)
from app.models.import_request import ImportRequest
from app.models.import_request_item import ImportRequestItem
from app.models.project import Project
from app.models.source import Source
from app.constants.import_constants import ImportRequestStatuses, ImportItemStatuses


@pytest.fixture
def process_request_command(db):
    """Create a ProcessImportRequestCommand instance for testing."""
    return ProcessImportRequestCommand(db)


class TestProcessImportRequestCommand:
    """Test cases for ProcessImportRequestCommand."""

    def test_execute_success(
        self,
        process_request_command,
        setup_import_request,
        setup_import_request_with_items,
        setup_project,
    ):
        """Test successful processing of an import request."""
        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Assertions
        assert result["success"] is True
        assert result["import_request_id"] == setup_import_request.id
        assert result["total_items"] == 3  # The fixture creates 3 items
        assert result["success_count"] == 0  # All items will fail due to invalid data
        assert result["failure_count"] == 3
        assert result["status"] == ImportRequestStatuses.COMPLETED_WITH_ERRORS
        assert len(result["processed_items"]) == 3
        assert len(result["errors"]) == 3

    def test_execute_with_failures(
        self, process_request_command, setup_import_request, setup_project, db
    ):
        """Test processing with some failures."""
        from app.schemas.project_import import ImportItemData, ImportAuthorData

        # Create one valid item and one invalid item
        source_id = setup_import_request.source_id

        # Valid item
        valid_item_data = ImportItemData(
            source="github",
            title="Valid Item",
            body="This is a valid item",
            tags=["test"],
            labels={"priority": "high"},
            author=ImportAuthorData(
                id="valid_author",
                display_name="Valid Author",
                email="valid@example.com",
                avatar_url="https://example.com/avatar.png",
                tags=["developer"],
                labels={"role": "maintainer"},
                meta_data={"github_username": "validauthor"},
            ),
        )

        # Invalid item (missing required fields)
        invalid_item_data = {"invalid": "data"}

        # Create items
        valid_item = ImportRequestItem(
            import_request_id=setup_import_request.id,
            source_id=source_id,
            source_item_id="valid_item",
            raw_payload=valid_item_data.model_dump(),
            status=ImportItemStatuses.FAILED,
        )

        invalid_item = ImportRequestItem(
            import_request_id=setup_import_request.id,
            source_id=source_id,
            source_item_id="invalid_item",
            raw_payload=invalid_item_data,
            status=ImportItemStatuses.FAILED,
        )

        db.add(valid_item)
        db.add(invalid_item)
        db.commit()
        db.refresh(valid_item)
        db.refresh(invalid_item)

        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Assertions
        assert result["success"] is True
        assert result["total_items"] == 2
        assert result["success_count"] == 1
        assert result["failure_count"] == 1
        assert result["status"] == ImportRequestStatuses.COMPLETED_WITH_ERRORS
        assert len(result["processed_items"]) == 2
        assert len(result["errors"]) == 1

    def test_execute_import_request_not_found(
        self, process_request_command, setup_project
    ):
        """Test processing when import request is not found."""
        # Execute the command with a non-existent import request ID
        result = process_request_command.execute(uuid4(), setup_project)

        # Assertions
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_execute_no_items(
        self, process_request_command, setup_import_request, setup_project, db
    ):
        """Test processing when no items are found."""
        # Delete all items for this import request
        db.query(ImportRequestItem).filter(
            ImportRequestItem.import_request_id == setup_import_request.id
        ).delete()
        db.commit()

        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Assertions
        assert result["success"] is False
        assert "No items found" in result["error"]

    def test_execute_with_exception(
        self, process_request_command, setup_import_request, setup_project, db
    ):
        """Test processing when an exception occurs during item processing."""
        # Create items with data that will cause processing errors
        source_id = setup_import_request.source_id

        # Create items with invalid data that will cause validation errors
        invalid_item1 = ImportRequestItem(
            import_request_id=setup_import_request.id,
            source_id=source_id,
            source_item_id="invalid_item_1",
            raw_payload={"invalid": "data1"},
            status=ImportItemStatuses.FAILED,
        )

        invalid_item2 = ImportRequestItem(
            import_request_id=setup_import_request.id,
            source_id=source_id,
            source_item_id="invalid_item_2",
            raw_payload={"invalid": "data2"},
            status=ImportItemStatuses.FAILED,
        )

        db.add(invalid_item1)
        db.add(invalid_item2)
        db.commit()
        db.refresh(invalid_item1)
        db.refresh(invalid_item2)

        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Assertions
        assert result["success"] is True  # Command itself succeeds
        assert result["total_items"] == 2
        assert result["success_count"] == 0
        assert result["failure_count"] == 2
        assert result["status"] == ImportRequestStatuses.COMPLETED_WITH_ERRORS
        assert len(result["errors"]) == 2

    def test_execute_batch_success(
        self,
        process_request_command,
        setup_project,
        db,
        setup_import_request,
        setup_source,
    ):
        """Test successful batch processing of multiple import requests."""
        from app.schemas.project_import import ImportItemData, ImportAuthorData

        # Create first import request with valid items
        import_request1 = setup_import_request

        # Create valid items for first request
        item_data = ImportItemData(
            source="github",
            title="Test Item",
            body="This is a test item",
            tags=["test"],
            labels={"priority": "high"},
            author=ImportAuthorData(
                id="test_author",
                display_name="Test Author",
                email="test@example.com",
                avatar_url="https://example.com/avatar.png",
                tags=["developer"],
                labels={"role": "maintainer"},
                meta_data={"github_username": "testauthor"},
            ),
        )

        item1 = ImportRequestItem(
            import_request_id=import_request1.id,
            source_id=import_request1.source_id,
            source_item_id="item_1",
            raw_payload=item_data.model_dump(),
            status=ImportItemStatuses.FAILED,
        )

        # Create second import request with valid items
        import_request2 = ImportRequest(
            source_id=import_request1.source_id,
            requested_by_id=import_request1.requested_by_id,
            status=ImportRequestStatuses.PROCESSING,
            received_count=1,
            success_count=0,
            failure_count=0,
            project_id=setup_project.id,
            options={},
        )
        db.add(import_request2)
        db.commit()
        db.refresh(import_request2)

        item2 = ImportRequestItem(
            import_request_id=import_request2.id,
            source_id=import_request1.source_id,
            source_item_id="item_2",
            raw_payload=item_data.model_dump(),
            status=ImportItemStatuses.FAILED,
        )

        db.add(item1)
        db.add(item2)
        db.commit()

        # Execute the batch command
        result = process_request_command.execute_batch(
            [import_request1.id, import_request2.id], setup_project
        )

        # Assertions
        assert result["success"] is True
        assert result["total_import_requests"] == 2
        assert result["total_items"] == 2  # 1 item from each request
        assert result["total_success"] == 2
        assert result["total_failure"] == 0
        assert len(result["results"]) == 2

    def test_execute_batch_with_failures(
        self,
        process_request_command,
        setup_project,
        db,
        setup_import_request,
        setup_source,
    ):
        """Test batch processing with some failures."""
        from app.schemas.project_import import ImportItemData, ImportAuthorData

        # Create first import request with valid item
        import_request1 = setup_import_request

        # Create valid item for first request
        valid_item_data = ImportItemData(
            source="github",
            title="Valid Item",
            body="This is a valid item",
            tags=["test"],
            labels={"priority": "high"},
            author=ImportAuthorData(
                id="valid_author",
                display_name="Valid Author",
                email="valid@example.com",
                avatar_url="https://example.com/avatar.png",
                tags=["developer"],
                labels={"role": "maintainer"},
                meta_data={"github_username": "validauthor"},
            ),
        )

        valid_item = ImportRequestItem(
            import_request_id=import_request1.id,
            source_id=import_request1.source_id,
            source_item_id="valid_item",
            raw_payload=valid_item_data.model_dump(),
            status=ImportItemStatuses.FAILED,
        )

        # Create second import request with invalid item
        import_request2 = ImportRequest(
            source_id=import_request1.source_id,
            requested_by_id=import_request1.requested_by_id,
            status=ImportRequestStatuses.PROCESSING,
            received_count=1,
            success_count=0,
            failure_count=0,
            project_id=setup_project.id,
            options={},
        )
        db.add(import_request2)
        db.commit()
        db.refresh(import_request2)

        # Create invalid item for second request
        invalid_item = ImportRequestItem(
            import_request_id=import_request2.id,
            source_id=import_request1.source_id,
            source_item_id="invalid_item",
            raw_payload={"invalid": "data"},
            status=ImportItemStatuses.FAILED,
        )

        db.add(valid_item)
        db.add(invalid_item)
        db.commit()

        # Execute the batch command
        result = process_request_command.execute_batch(
            [import_request1.id, import_request2.id], setup_project
        )

        # Assertions
        assert result["success"] is True
        assert result["total_import_requests"] == 2
        assert (
            result["total_items"] == 2
        )  # 1 valid item from first request + 1 invalid from second
        assert result["total_success"] == 1  # Only the 1 valid item from first request
        assert result["total_failure"] == 1  # 1 invalid item from second request
        assert len(result["results"]) == 2

    def test_status_updates(
        self,
        process_request_command,
        setup_import_request,
        setup_import_request_with_items,
        setup_project,
        db,
    ):
        """Test that import request status is updated correctly."""
        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Verify the result shows processing with errors (due to invalid fixture data)
        assert result["success"] is True
        assert result["status"] == ImportRequestStatuses.COMPLETED_WITH_ERRORS
        assert result["success_count"] == 0
        assert result["failure_count"] == 3

        # Verify the import request was updated in the database
        updated_request = (
            db.query(ImportRequest)
            .filter(ImportRequest.id == setup_import_request.id)
            .first()
        )
        assert updated_request.status == ImportRequestStatuses.COMPLETED_WITH_ERRORS
        assert updated_request.success_count == 0
        assert updated_request.failure_count == 3

    def test_processed_items_structure(
        self,
        process_request_command,
        setup_import_request,
        setup_import_request_with_items,
        setup_project,
    ):
        """Test the structure of processed items in the result."""
        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Check processed items structure
        assert len(result["processed_items"]) == 3

        for item in result["processed_items"]:
            assert "item_id" in item
            assert "success" in item
            assert (
                item["success"] is False
            )  # All items will fail due to invalid fixture data
            assert "error" in item
            assert item.get("author_id") is None  # No author_id for failed items
            assert item.get("entry_id") is None  # No entry_id for failed items
            assert item.get("comment_ids") == []  # Empty list for failed items
            assert (
                item.get("source_author_id") is None
            )  # No source_author_id for failed items

    def test_processed_items_with_errors(
        self, process_request_command, setup_import_request, setup_project, db
    ):
        """Test the structure of processed items when there are errors."""
        # Create items with invalid data that will cause processing errors
        source_id = setup_import_request.source_id

        # Delete existing items and create invalid ones
        db.query(ImportRequestItem).filter(
            ImportRequestItem.import_request_id == setup_import_request.id
        ).delete()

        invalid_item1 = ImportRequestItem(
            import_request_id=setup_import_request.id,
            source_id=source_id,
            source_item_id="invalid_item_1",
            raw_payload={"invalid": "data1"},
            status=ImportItemStatuses.FAILED,
        )

        invalid_item2 = ImportRequestItem(
            import_request_id=setup_import_request.id,
            source_id=source_id,
            source_item_id="invalid_item_2",
            raw_payload={"invalid": "data2"},
            status=ImportItemStatuses.FAILED,
        )

        db.add(invalid_item1)
        db.add(invalid_item2)
        db.commit()

        # Execute the command
        result = process_request_command.execute(setup_import_request.id, setup_project)

        # Check processed items structure
        assert len(result["processed_items"]) == 2

        for item in result["processed_items"]:
            assert "item_id" in item
            assert "success" in item
            assert item["success"] is False
            assert "error" in item
            assert item.get("author_id") is None  # No author_id for failed items
