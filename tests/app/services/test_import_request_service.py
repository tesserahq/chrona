from uuid import uuid4
from app.services.import_request_service import ImportRequestService
from app.schemas.import_request import (
    ImportRequestCreate,
    ImportRequestUpdate,
)
from app.schemas.import_request_item import (
    ImportRequestItemCreate,
    ImportRequestItemUpdate,
)


class TestImportRequestService:
    """Test cases for ImportRequestService."""

    def test_get_import_request(self, db, setup_import_request):
        """Test getting a single import request by ID."""
        service = ImportRequestService(db)
        result = service.get_import_request(setup_import_request.id)

        assert result is not None
        assert result.id == setup_import_request.id
        assert result.source == setup_import_request.source
        assert result.status == setup_import_request.status

    def test_get_import_request_not_found(self, db):
        """Test getting a non-existent import request."""
        service = ImportRequestService(db)
        result = service.get_import_request(uuid4())
        assert result is None

    def test_get_import_requests(
        self, db, setup_import_request, setup_another_import_request
    ):
        """Test getting a list of import requests."""
        service = ImportRequestService(db)
        results = service.get_import_requests()

        assert len(results) >= 2
        ids = [r.id for r in results]
        assert setup_import_request.id in ids
        assert setup_another_import_request.id in ids

    def test_get_import_requests_pagination(
        self, db, setup_import_request, setup_another_import_request
    ):
        """Test pagination for getting import requests."""
        service = ImportRequestService(db)

        # Test first page
        results = service.get_import_requests(skip=0, limit=1)
        assert len(results) == 1

        # Test second page
        results = service.get_import_requests(skip=1, limit=1)
        assert len(results) == 1

    def test_get_import_requests_by_project(
        self, db, setup_import_request, setup_project
    ):
        """Test getting import requests by project ID."""
        service = ImportRequestService(db)
        results = service.get_import_requests_by_project(setup_project.id)

        assert len(results) >= 1
        assert all(r.project_id == setup_project.id for r in results)

    def test_get_import_requests_by_user(self, db, setup_user, setup_import_request):
        """Test getting import requests by user ID."""
        user = setup_user
        service = ImportRequestService(db)
        results = service.get_import_requests_by_user(setup_user.id)

        assert len(results) >= 1
        assert all(r.requested_by_id == user.id for r in results)

    def test_create_import_request(
        self, db, setup_user, setup_project, setup_source, faker
    ):
        """Test creating a new import request."""
        source = setup_source
        user = setup_user
        project = setup_project
        service = ImportRequestService(db)
        import_request_data = ImportRequestCreate(
            source_id=source.id,
            requested_by_id=user.id,
            status="pending",
            received_count=10,
            success_count=0,
            failure_count=0,
            options={"format": "csv"},
            project_id=project.id,
        )

        result = service.create_import_request(import_request_data)

        assert result is not None
        assert result.source_id == source.id
        assert result.requested_by_id == user.id
        assert result.status == "pending"
        assert result.project_id == project.id

    def test_update_import_request(self, db, setup_import_request):
        """Test updating an import request."""
        service = ImportRequestService(db)
        update_data = ImportRequestUpdate(
            status="completed",
            success_count=5,
            failure_count=2,
        )

        result = service.update_import_request(setup_import_request.id, update_data)

        assert result is not None
        assert result.status == "completed"
        assert result.success_count == 5
        assert result.failure_count == 2

    def test_update_import_request_not_found(self, db):
        """Test updating a non-existent import request."""
        service = ImportRequestService(db)
        update_data = ImportRequestUpdate(status="completed")

        result = service.update_import_request(uuid4(), update_data)
        assert result is None

    def test_delete_import_request(self, db, setup_import_request):
        """Test soft deleting an import request."""
        service = ImportRequestService(db)
        result = service.delete_import_request(setup_import_request.id)

        assert result is True

        # Verify it's soft deleted
        deleted_request = service.get_import_request(setup_import_request.id)
        assert deleted_request is None

    def test_delete_import_request_not_found(self, db):
        """Test deleting a non-existent import request."""
        service = ImportRequestService(db)
        result = service.delete_import_request(uuid4())
        assert result is False

    def test_search_import_requests(
        self, db, setup_import_request, setup_another_import_request
    ):
        """Test searching import requests with filters."""
        service = ImportRequestService(db)

        # Search by status
        results = service.search({"status": "pending"})
        assert len(results) >= 1
        assert all(r.status == "pending" for r in results)

        # Search by source
        results = service.search({"source": setup_import_request.source})
        assert len(results) >= 1
        assert any(r.source == setup_import_request.source for r in results)

    def test_search_import_requests_with_operator(self, db, setup_import_request):
        """Test searching import requests with operators."""
        service = ImportRequestService(db)

        # Search with ilike operator
        results = service.search(
            {
                "status": {
                    "operator": "ilike",
                    "value": f"%{setup_import_request.status}%",
                }
            }
        )
        assert len(results) >= 1
        assert any(r.status == setup_import_request.status for r in results)

    def test_get_import_request_items(self, db, setup_import_request_with_items):
        """Test getting items for an import request."""
        service = ImportRequestService(db)
        import_request, items = setup_import_request_with_items

        results = service.get_import_request_items(import_request.id)

        assert len(results) == 3
        assert all(item.import_request_id == import_request.id for item in results)

    def test_create_import_request_item(
        self, db, setup_import_request, setup_source, faker
    ):
        """Test creating a new import request item."""
        source = setup_source
        import_request = setup_import_request

        service = ImportRequestService(db)
        item_data = ImportRequestItemCreate(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id=faker.uuid4(),
            raw_payload={"title": "Test Item"},
            status="pending",
        )

        result = service.create_import_request_item(item_data)

        assert result is not None
        assert result.import_request_id == setup_import_request.id
        assert result.source.id == source.id
        assert result.status == "pending"

    def test_update_import_request_item(self, db, setup_import_request_item):
        """Test updating an import request item."""
        service = ImportRequestService(db)
        update_data = ImportRequestItemUpdate(
            status="completed",
            success_count=1,
        )

        result = service.update_import_request_item(
            setup_import_request_item.id, update_data
        )

        assert result is not None
        assert result.status == "completed"

    def test_delete_import_request_item(self, db, setup_import_request_item):
        """Test soft deleting an import request item."""
        service = ImportRequestService(db)
        result = service.delete_import_request_item(setup_import_request_item.id)

        assert result is True

    def test_search_import_request_items(self, db, setup_import_request_with_items):
        """Test searching import request items with filters."""
        service = ImportRequestService(db)
        import_request, items = setup_import_request_with_items

        # Search by import request ID
        results = service.search_items({"import_request_id": import_request.id})
        assert len(results) == 3

        # Search by status
        results = service.search_items({"status": "pending"})
        assert len(results) >= 1
        assert all(item.status == "pending" for item in results)

    def test_get_import_request_stats(self, db, setup_import_request_with_items):
        """Test getting statistics for an import request."""
        service = ImportRequestService(db)
        import_request, items = setup_import_request_with_items

        stats = service.get_import_request_stats(import_request.id)

        assert stats is not None
        assert stats["import_request_id"] == import_request.id
        assert stats["total_items"] == 3
        assert "status_counts" in stats
        assert "completion_rate" in stats

    def test_get_import_request_stats_not_found(self, db):
        """Test getting statistics for a non-existent import request."""
        service = ImportRequestService(db)
        stats = service.get_import_request_stats(uuid4())
        assert stats is None

    def test_import_request_stats_completion_rate(
        self, db, setup_user, setup_project, setup_source, faker
    ):
        """Test completion rate calculation in stats."""
        service = ImportRequestService(db)
        source = setup_source
        user = setup_user
        project = setup_project
        # Create import request with known counts
        import_request_data = ImportRequestCreate(
            source_id=source.id,
            requested_by_id=user.id,
            status="completed",
            received_count=10,
            success_count=8,
            failure_count=2,
            project_id=project.id,
        )
        import_request = service.create_import_request(import_request_data)

        stats = service.get_import_request_stats(import_request.id)

        assert stats["completion_rate"] == 80.0  # 8/10 * 100

    def test_import_request_stats_zero_division(
        self, db, setup_user, setup_project, setup_source
    ):
        """Test completion rate calculation when received_count is 0."""
        service = ImportRequestService(db)
        source = setup_source
        user = setup_user
        project = setup_project

        # Create import request with zero received count
        import_request_data = ImportRequestCreate(
            source_id=source.id,
            requested_by_id=user.id,
            status="pending",
            received_count=0,
            success_count=0,
            failure_count=0,
            project_id=project.id,
        )
        import_request = service.create_import_request(import_request_data)

        stats = service.get_import_request_stats(import_request.id)

        assert stats["completion_rate"] == 0.0
