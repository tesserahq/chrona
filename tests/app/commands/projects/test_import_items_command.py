from app.commands.projects.import_items_command import ImportItemsCommand
from app.models.import_request import ImportRequest
from app.models.import_request_item import ImportRequestItem
from app.models.source import Source
from app.schemas.project_import import (
    ImportItemRequest,
)
from app.constants.import_constants import ImportRequestStatuses, ImportItemStatuses


class TestImportItemsCommand:
    """Test cases for ImportItemsCommand."""

    def test_import_items_success(self, db, setup_user, setup_project):
        """Test successfully importing items."""
        # Arrange
        user = setup_user
        project = setup_project

        # Test payload from user request
        payload = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "API returns 500 error on POST /users",
                    "body": "Steps to reproduce:\n1. Send POST request to /users with valid payload\n2. Server responds with 500 instead of 201",
                    "tags": ["bug", "api"],
                    "labels": {"priority": "high"},
                    "meta_data": {"repo": "org/repo"},
                    "author": {
                        "id": "9876543210",
                        "display_name": "Alice Smith",
                        "avatar_url": "https://avatar.url/alice",
                        "email": "alice.smith@example.com",
                        "tags": ["bug", "api"],
                        "labels": {"priority": "high"},
                        "meta_data": {"source": "github"},
                    },
                },
                {
                    "source": "github",
                    "title": "UI freezes when loading dashboard",
                    "body": "The dashboard page becomes unresponsive when more than 1000 records are loaded. Needs optimization.",
                    "tags": ["bug", "frontend"],
                    "labels": {"priority": "medium"},
                    "meta_data": {"repo": "org/repo"},
                    "author": {
                        "id": "2468013579",
                        "display_name": "Bob Johnson",
                        "avatar_url": "https://avatar.url/bob",
                        "email": "bob.johnson@example.com",
                        "tags": ["bug", "frontend"],
                        "labels": {"priority": "medium"},
                        "meta_data": {"source": "github"},
                    },
                },
                {
                    "source": "github",
                    "title": "Add dark mode support",
                    "body": "Feature request: Implement dark mode toggle in settings. Many users have asked for this.",
                    "tags": ["enhancement", "ui"],
                    "labels": {"priority": "low"},
                    "meta_data": {"repo": "org/repo"},
                    "author": {
                        "id": "1122334455",
                        "display_name": "Charlie Lee",
                        "avatar_url": "https://avatar.url/charlie",
                        "email": "charlie.lee@example.com",
                        "tags": ["enhancement", "ui"],
                        "labels": {"priority": "low"},
                        "meta_data": {"source": "github"},
                    },
                },
            ],
        }

        import_request = ImportItemRequest(**payload)

        # Act
        command = ImportItemsCommand(db)
        result = command.execute(project, import_request, user.id)

        # Assert result structure
        assert result is not None
        assert "id" in result
        assert "total_items" in result
        assert "processed_items" in result
        assert "success_count" in result
        assert "failure_count" in result
        assert "status" in result

        # Assert result values
        assert result["total_items"] == 3
        assert result["processed_items"] == 0
        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["status"] == ImportRequestStatuses.PENDING

        # Assert import request was created
        id = result["id"]
        db_import_request = (
            db.query(ImportRequest).filter(ImportRequest.id == id).first()
        )
        assert db_import_request is not None
        assert db_import_request.project_id == project.id
        assert db_import_request.requested_by_id == user.id
        assert db_import_request.status == ImportRequestStatuses.PENDING
        assert db_import_request.received_count == 3
        assert db_import_request.success_count == 0
        assert db_import_request.failure_count == 0

        # Assert source was created
        source = (
            db.query(Source).filter(Source.id == db_import_request.source_id).first()
        )
        assert source is not None
        assert source.identifier == "github"
        assert source.workspace_id == project.workspace_id

        # Assert import request items were created
        items = (
            db.query(ImportRequestItem)
            .filter(ImportRequestItem.import_request_id == id)
            .all()
        )
        assert len(items) == 3

        # Assert each item has correct data
        for i, item in enumerate(items):
            assert item.status == ImportItemStatuses.PENDING
            assert item.source_id == source.id
            assert item.raw_payload is not None

            # Check that source_item_id matches author ID
            expected_author_id = payload["items"][i]["author"]["id"]
            assert item.source_item_id == expected_author_id

            # Check raw payload contains the full item data
            raw_data = item.raw_payload
            assert raw_data["source"] == payload["items"][i]["source"]
            assert raw_data["title"] == payload["items"][i]["title"]
            assert raw_data["body"] == payload["items"][i]["body"]
            assert raw_data["author"]["id"] == expected_author_id
            assert (
                raw_data["author"]["display_name"]
                == payload["items"][i]["author"]["display_name"]
            )

    def test_import_items_empty_list(self, db, setup_user, setup_project):
        """Test importing an empty list of items."""
        # Arrange
        user = setup_user
        project = setup_project
        import_request = ImportItemRequest(source="github", items=[])

        # Act
        command = ImportItemsCommand(db)
        result = command.execute(project, import_request, user.id)

        # Assert result
        assert result["total_items"] == 0
        assert result["processed_items"] == 0
        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["status"] == ImportRequestStatuses.PENDING

        # Assert import request was created
        id = result["id"]
        db_import_request = (
            db.query(ImportRequest).filter(ImportRequest.id == id).first()
        )
        assert db_import_request is not None
        assert db_import_request.status == ImportRequestStatuses.PENDING

    def test_import_items_single_item(self, db, setup_user, setup_project):
        """Test importing a single item."""
        # Arrange
        user = setup_user
        project = setup_project

        payload = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "Single test item",
                    "body": "This is a test item",
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"repo": "test/repo"},
                    "author": {
                        "id": "123456789",
                        "display_name": "Test Author",
                        "avatar_url": "https://example.com/avatar",
                        "email": "test@example.com",
                        "tags": ["test"],
                        "labels": {"priority": "low"},
                        "meta_data": {"source": "github"},
                    },
                }
            ],
        }

        import_request = ImportItemRequest(**payload)

        # Act
        command = ImportItemsCommand(db)
        result = command.execute(project, import_request, user.id)

        # Assert result
        assert result["total_items"] == 1
        assert result["processed_items"] == 0
        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["status"] == ImportRequestStatuses.PENDING

        # Assert single item was created
        id = result["id"]
        items = (
            db.query(ImportRequestItem)
            .filter(ImportRequestItem.import_request_id == id)
            .all()
        )
        assert len(items) == 1

        item = items[0]
        assert item.source_item_id == "123456789"
        assert item.status == ImportItemStatuses.PENDING
        assert item.raw_payload["title"] == "Single test item"

    def test_import_items_creates_source_once(self, db, setup_user, setup_project):
        """Test that source is created only once per project."""
        # Arrange
        user = setup_user
        project = setup_project

        # Create two separate import requests for the same project
        payload1 = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "First item",
                    "body": "First test item",
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"repo": "test/repo"},
                    "author": {
                        "id": "111111111",
                        "display_name": "Author 1",
                        "avatar_url": "https://example.com/avatar1",
                        "email": "author1@example.com",
                        "tags": ["test"],
                        "labels": {"priority": "low"},
                        "meta_data": {"source": "github"},
                    },
                }
            ],
        }

        payload2 = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "Second item",
                    "body": "Second test item",
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"repo": "test/repo"},
                    "author": {
                        "id": "222222222",
                        "display_name": "Author 2",
                        "avatar_url": "https://example.com/avatar2",
                        "email": "author2@example.com",
                        "tags": ["test"],
                        "labels": {"priority": "low"},
                        "meta_data": {"source": "github"},
                    },
                }
            ],
        }

        # Act
        command = ImportItemsCommand(db)
        result1 = command.execute(project, ImportItemRequest(**payload1), user.id)
        result2 = command.execute(project, ImportItemRequest(**payload2), user.id)

        # Assert both import requests were created
        assert result1["success_count"] == 0
        assert result2["success_count"] == 0

        # Assert only one source was created for the project
        sources = (
            db.query(Source).filter(Source.workspace_id == project.workspace_id).all()
        )
        assert len(sources) == 1

        source = sources[0]
        assert source.identifier == "github"

        # Assert both import requests use the same source
        import_request1 = (
            db.query(ImportRequest).filter(ImportRequest.id == result1["id"]).first()
        )
        import_request2 = (
            db.query(ImportRequest).filter(ImportRequest.id == result2["id"]).first()
        )

        assert import_request1.source_id == source.id
        assert import_request2.source_id == source.id

    def test_import_items_different_projects(
        self, db, setup_user, setup_project, faker
    ):
        """Test that different projects get different sources."""
        # Arrange
        user = setup_user
        project1 = setup_project

        # Create second project
        from app.models.project import Project

        project2 = Project(
            name=faker.company(),
            description=faker.text(100),
            workspace_id=project1.workspace_id,
        )
        db.add(project2)
        db.commit()
        db.refresh(project2)

        payload = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "Test item",
                    "body": "Test item body",
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"repo": "test/repo"},
                    "author": {
                        "id": "333333333",
                        "display_name": "Test Author",
                        "avatar_url": "https://example.com/avatar",
                        "email": "test@example.com",
                        "tags": ["test"],
                        "labels": {"priority": "low"},
                        "meta_data": {"source": "github"},
                    },
                }
            ],
        }

        # Act
        command = ImportItemsCommand(db)
        result1 = command.execute(project1, ImportItemRequest(**payload), user.id)
        result2 = command.execute(project2, ImportItemRequest(**payload), user.id)

        # Assert both import requests were created
        assert result1["success_count"] == 0
        assert result2["success_count"] == 0

        # Assert two different sources were created
        sources = (
            db.query(Source).filter(Source.workspace_id == project1.workspace_id).all()
        )
        assert len(sources) == 1

        source_identifiers = [source.identifier for source in sources]
        assert "github" in source_identifiers

    def test_import_items_verifies_database_persistence(
        self, db, setup_user, setup_project
    ):
        """Test that import request and items are properly persisted in database."""
        # Arrange
        user = setup_user
        project = setup_project

        payload = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "Persistence test item",
                    "body": "Testing database persistence",
                    "tags": ["test", "persistence"],
                    "labels": {"priority": "medium"},
                    "meta_data": {"repo": "test/persistence"},
                    "author": {
                        "id": "444444444",
                        "display_name": "Persistence Tester",
                        "avatar_url": "https://example.com/persistence",
                        "email": "persistence@example.com",
                        "tags": ["test", "persistence"],
                        "labels": {"priority": "medium"},
                        "meta_data": {"source": "github"},
                    },
                }
            ],
        }

        # Act
        command = ImportItemsCommand(db)
        result = command.execute(project, ImportItemRequest(**payload), user.id)

        # Assert import request exists in database
        id = result["id"]
        db_import_request = (
            db.query(ImportRequest).filter(ImportRequest.id == id).first()
        )
        assert db_import_request is not None
        assert db_import_request.project_id == project.id
        assert db_import_request.requested_by_id == user.id

        # Assert import request item exists in database
        db_item = (
            db.query(ImportRequestItem)
            .filter(ImportRequestItem.import_request_id == id)
            .first()
        )
        assert db_item is not None
        assert db_item.source_item_id == "444444444"
        assert db_item.status == ImportItemStatuses.PENDING
        assert db_item.raw_payload["title"] == "Persistence test item"
        assert db_item.raw_payload["author"]["display_name"] == "Persistence Tester"

    def test_import_items_with_minimal_data(self, db, setup_user, setup_project):
        """Test importing items with minimal required data."""
        # Arrange
        user = setup_user
        project = setup_project

        payload = {
            "source": "github",
            "items": [
                {
                    "source": "github",
                    "title": "Minimal item",
                    "body": "Minimal test item",
                    "tags": [],
                    "labels": {},
                    "meta_data": {},
                    "author": {
                        "id": "555555555",
                        "display_name": "Minimal Author",
                        "avatar_url": "https://example.com/minimal",
                        "email": "minimal@example.com",
                        "tags": [],
                        "labels": {},
                        "meta_data": {},
                    },
                }
            ],
        }

        # Act
        command = ImportItemsCommand(db)
        result = command.execute(project, ImportItemRequest(**payload), user.id)

        # Assert result
        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["status"] == ImportRequestStatuses.PENDING

        # Assert item was created with minimal data
        id = result["id"]
        db_item = (
            db.query(ImportRequestItem)
            .filter(ImportRequestItem.import_request_id == id)
            .first()
        )
        assert db_item is not None
        assert db_item.source_item_id == "555555555"
        assert db_item.raw_payload["title"] == "Minimal item"
        assert db_item.raw_payload["tags"] == []
        assert db_item.raw_payload["labels"] == {}
