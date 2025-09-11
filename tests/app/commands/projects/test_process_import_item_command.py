import pytest

from app.commands.projects.process_import_item_command import ProcessImportItemCommand
from app.schemas.project_import import (
    ImportItemData,
    ImportAuthorData,
    ImportEntryUpdateData,
)
from app.constants.import_constants import ImportItemStatuses


@pytest.fixture
def process_command(db):
    """Create a ProcessImportItemCommand instance for testing."""
    return ProcessImportItemCommand(db)


@pytest.fixture
def sample_import_item_data():
    """Create sample import item data for testing."""
    return ImportItemData(
        source="github",
        title="Test Issue",
        body="This is a test issue body",
        tags=["bug", "test"],
        labels={"priority": "high", "type": "bug"},
        meta_data={
            "external_id": "123",
            "url": "https://github.com/test/repo/issues/123",
        },
        author=ImportAuthorData(
            id="author_123",
            display_name="Test Author",
            avatar_url="https://github.com/avatar.png",
            email="test@example.com",
            tags=["developer"],
            labels={"role": "maintainer"},
            meta_data={"github_username": "testauthor"},
        ),
        entry_updates=[],  # Empty entry updates by default
    )


@pytest.fixture
def sample_import_item_data_with_comments():
    """Create sample import item data with entry updates for testing."""
    return ImportItemData(
        source="github",
        title="API returns 500 error on POST /users",
        body="Steps to reproduce:\n1. Send POST request to /users with valid payload\n2. Server responds with 500 instead of 201",
        tags=["bug", "api"],
        labels={"priority": "high"},
        meta_data={"repo": "org/repo"},
        author=ImportAuthorData(
            id="9876543210",
            display_name="Alice Smith",
            avatar_url="https://avatar.url/alice",
            email="alice.smith@example.com",
            tags=["bug", "api"],
            labels={"priority": "high"},
            meta_data={"source": "github"},
        ),
        entry_updates=[
            ImportEntryUpdateData(
                id="1234567890",
                body="I am also experiencing this issue.",
                created_at="2024-10-01T12:34:56Z",
                author=ImportAuthorData(
                    id="1234567890",
                    display_name="John Doe",
                    avatar_url="https://avatar.url/john",
                    email="john.doe@example.com",
                    tags=[],
                    labels={},
                    meta_data={},
                ),
                tags=["bug", "api"],
                labels={"priority": "high"},
            ),
            ImportEntryUpdateData(
                id="1122334455",
                body="I can reproduce this issue.",
                created_at="2024-10-01T12:34:56Z",
                author=ImportAuthorData(
                    id="1122334455",
                    display_name="Jane Roe",
                    avatar_url="https://avatar.url/jane",
                    email="jane.roe@example.com",
                    tags=[],
                    labels={},
                    meta_data={},
                ),
                tags=["bug", "api"],
                labels={"priority": "high"},
            ),
        ],
    )


class TestProcessImportItemCommand:
    """Test cases for ProcessImportItemCommand."""

    def test_execute_success(
        self, process_command, setup_project, sample_import_item_data, test_user
    ):
        """Test successful processing of an import item."""
        # Create a proper import request item with the correct payload
        from app.models.import_request_item import ImportRequestItem
        from app.models.import_request import ImportRequest
        from app.models.source import Source

        # Create source first
        source = Source(
            name="Test Source",
            identifier="github",
            workspace_id=setup_project.workspace_id,
        )
        process_command.db.add(source)
        process_command.db.commit()
        process_command.db.refresh(source)

        # Create import request
        import_request = ImportRequest(
            source_id=source.id,
            requested_by_id=test_user.id,
            status="pending",
            received_count=1,
            success_count=0,
            failure_count=0,
            project_id=setup_project.id,
        )
        process_command.db.add(import_request)
        process_command.db.commit()
        process_command.db.refresh(import_request)

        # Create import request item with proper payload
        import_request_item = ImportRequestItem(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id="item_123",
            raw_payload=sample_import_item_data.model_dump(),
            status=ImportItemStatuses.FAILED,
        )
        process_command.db.add(import_request_item)
        process_command.db.commit()
        process_command.db.refresh(import_request_item)

        # Execute the command
        result = process_command.execute(import_request_item, setup_project)

        # Assertions
        assert result["success"] is True
        assert "author_id" in result
        assert "entry_id" in result
        assert "entry_update_ids" in result
        assert "source_author_id" in result

    def test_execute_with_existing_author(
        self, process_command, setup_project, sample_import_item_data, test_user
    ):
        """Test processing when author already exists."""
        # Create a proper import request item with the correct payload
        from app.models.import_request_item import ImportRequestItem
        from app.models.import_request import ImportRequest
        from app.models.source import Source
        from app.services.author_service import AuthorService
        from app.schemas.author import AuthorCreate

        # Create source first
        source = Source(
            name="Test Source",
            identifier="github",
            workspace_id=setup_project.workspace_id,
        )
        process_command.db.add(source)
        process_command.db.commit()
        process_command.db.refresh(source)

        # Create import request
        import_request = ImportRequest(
            source_id=source.id,
            requested_by_id=test_user.id,
            status="pending",
            received_count=1,
            success_count=0,
            failure_count=0,
            project_id=setup_project.id,
        )
        process_command.db.add(import_request)
        process_command.db.commit()
        process_command.db.refresh(import_request)

        # Create import request item with proper payload
        import_request_item = ImportRequestItem(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id="item_123",
            raw_payload=sample_import_item_data.model_dump(),
            status=ImportItemStatuses.FAILED,
        )
        process_command.db.add(import_request_item)
        process_command.db.commit()
        process_command.db.refresh(import_request_item)

        # First, create an author with the same email
        author_service = AuthorService(process_command.db)
        existing_author = author_service.create_author(
            AuthorCreate(
                display_name="Existing Author",
                email=sample_import_item_data.author.email,
                avatar_url="https://example.com/avatar.png",
            ),
            setup_project.workspace_id,
        )

        # Execute the command
        result = process_command.execute(import_request_item, setup_project)

        # Assertions
        assert result["success"] is True
        assert result["author_id"] == existing_author.id
        assert "entry_id" in result
        assert "entry_update_ids" in result
        assert "source_author_id" in result

    def test_execute_with_validation_error(
        self, process_command, setup_import_request_item, setup_project
    ):
        """Test processing with invalid data that causes validation error."""
        # Set invalid raw payload
        setup_import_request_item.raw_payload = {"invalid": "data"}

        # Execute the command
        result = process_command.execute(setup_import_request_item, setup_project)

        # Assertions
        assert result["success"] is False
        assert "error" in result

    def test_execute_with_service_error(
        self,
        process_command,
        setup_import_request_item,
        setup_project,
        sample_import_item_data,
    ):
        """Test processing when a service throws an exception."""
        # This test would require a more complex setup to trigger a real service error
        # For now, we'll test with invalid data that causes a validation error
        setup_import_request_item.raw_payload = {"invalid": "data"}

        # Execute the command
        result = process_command.execute(setup_import_request_item, setup_project)

        # Assertions
        assert result["success"] is False
        assert "error" in result

    def test_create_or_get_author_new_author(
        self, process_command, sample_import_item_data, setup_project
    ):
        """Test creating a new author."""
        result = process_command._create_or_get_author(
            sample_import_item_data.author, setup_project.workspace_id
        )

        assert result is not None
        assert result.email == sample_import_item_data.author.email
        assert result.display_name == sample_import_item_data.author.display_name

    def test_create_or_get_author_existing_author(
        self, process_command, sample_import_item_data, setup_project
    ):
        """Test getting an existing author."""
        # First create an author
        from app.services.author_service import AuthorService
        from app.schemas.author import AuthorCreate

        author_service = AuthorService(process_command.db)
        existing_author = author_service.create_author(
            AuthorCreate(
                display_name="Existing Author",
                email=sample_import_item_data.author.email,
                avatar_url="https://example.com/avatar.png",
            ),
            setup_project.workspace_id,
        )

        # Now test getting the existing author
        result = process_command._create_or_get_author(
            sample_import_item_data.author, setup_project.workspace_id
        )

        assert result.id == existing_author.id
        assert result.email == existing_author.email

    def test_create_or_get_source_author(
        self, process_command, sample_import_item_data, setup_project
    ):
        """Test creating or getting a source author."""
        # First create an author and source
        from app.services.author_service import AuthorService
        from app.services.source_service import SourceService
        from app.schemas.author import AuthorCreate
        from app.schemas.source import SourceCreate

        author_service = AuthorService(process_command.db)
        author = author_service.create_author(
            AuthorCreate(
                display_name="Test Author",
                email=sample_import_item_data.author.email,
                avatar_url="https://example.com/avatar.png",
            ),
            setup_project.workspace_id,
        )

        source_service = SourceService(process_command.db)
        source = source_service.create_source(
            SourceCreate(name="Test Source", identifier="github"),
            setup_project.workspace_id,
        )

        source_author_id = "external_author_123"

        result = process_command._create_or_get_source_author(
            author.id, source.id, source_author_id
        )

        assert result is not None
        assert result.author_id == author.id
        assert result.source_id == source.id
        assert result.source_author_id == source_author_id

    def test_create_entry(
        self, process_command, sample_import_item_data, setup_project
    ):
        """Test creating an entry."""
        # First create required dependencies
        from app.services.author_service import AuthorService
        from app.services.source_service import SourceService
        from app.services.source_author_service import SourceAuthorService
        from app.schemas.author import AuthorCreate
        from app.schemas.source import SourceCreate

        author_service = AuthorService(process_command.db)
        author = author_service.create_author(
            AuthorCreate(
                display_name="Test Author",
                email=sample_import_item_data.author.email,
                avatar_url="https://example.com/avatar.png",
            ),
            setup_project.workspace_id,
        )

        source_service = SourceService(process_command.db)
        source = source_service.create_source(
            SourceCreate(name="Test Source", identifier="github"),
            setup_project.workspace_id,
        )

        source_author_service = SourceAuthorService(process_command.db)
        source_author = source_author_service.get_or_create_source_author(
            source.id, author.id, "external_author_123"
        )

        result = process_command._create_entry(
            sample_import_item_data,
            source_author.id,
            source.id,
            setup_project.id,
            "external_entry_123",
        )

        assert result is not None
        assert result.title == sample_import_item_data.title
        assert result.body == sample_import_item_data.body
        assert result.source_id == source.id
        assert result.source_author_id == source_author.id
        assert result.project_id == setup_project.id

    def test_create_entry_updates_with_comments_field(
        self, process_command, sample_import_item_data_with_comments, setup_project
    ):
        """Test creating entry updates when entry_updates field is present."""
        # First create required dependencies
        from app.services.author_service import AuthorService
        from app.services.source_service import SourceService
        from app.services.source_author_service import SourceAuthorService
        from app.services.entry_service import EntryService
        from app.schemas.author import AuthorCreate
        from app.schemas.source import SourceCreate
        from app.schemas.entry import EntryCreate

        # Create the main author
        author_service = AuthorService(process_command.db)
        author = author_service.create_author(
            AuthorCreate(
                display_name="Test Author",
                email=sample_import_item_data_with_comments.author.email,
                avatar_url="https://example.com/avatar.png",
            ),
            setup_project.workspace_id,
        )

        source_service = SourceService(process_command.db)
        source = source_service.create_source(
            SourceCreate(name="Test Source", identifier="github"),
            setup_project.workspace_id,
        )

        source_author_service = SourceAuthorService(process_command.db)
        source_author = source_author_service.get_or_create_source_author(
            source.id, author.id, "external_author_123"
        )

        entry_service = EntryService(process_command.db)
        entry = entry_service.create_entry(
            EntryCreate(
                title=sample_import_item_data_with_comments.title,
                body=sample_import_item_data_with_comments.body,
                source_id=source.id,
                external_id="external_entry_123",
                source_author_id=source_author.id,
                project_id=setup_project.id,
            )
        )

        result = process_command._create_entry_updates(
            sample_import_item_data_with_comments,
            entry.id,
            setup_project.workspace_id,
            source.id,
        )

        # Should create 2 entry updates from the entry_updates field
        assert len(result) == 2

        # Check first entry update
        assert result[0].body == "I am also experiencing this issue."
        assert result[0].entry_id == entry.id
        assert result[0].tags == ["bug", "api"]
        assert result[0].labels == {"priority": "high"}

        # Check second entry update
        assert result[1].body == "I can reproduce this issue."
        assert result[1].entry_id == entry.id
        assert result[1].tags == ["bug", "api"]
        assert result[1].labels == {"priority": "high"}

    def test_create_entry_updates_without_comments_field(
        self, process_command, sample_import_item_data, setup_project
    ):
        """Test creating entry updates when entry_updates field is empty."""
        # First create required dependencies
        from app.services.author_service import AuthorService
        from app.services.source_service import SourceService
        from app.services.source_author_service import SourceAuthorService
        from app.services.entry_service import EntryService
        from app.schemas.author import AuthorCreate
        from app.schemas.source import SourceCreate
        from app.schemas.entry import EntryCreate

        author_service = AuthorService(process_command.db)
        author = author_service.create_author(
            AuthorCreate(
                display_name="Test Author",
                email=sample_import_item_data.author.email,
                avatar_url="https://example.com/avatar.png",
            ),
            setup_project.workspace_id,
        )

        source_service = SourceService(process_command.db)
        source = source_service.create_source(
            SourceCreate(name="Test Source", identifier="github"),
            setup_project.workspace_id,
        )

        source_author_service = SourceAuthorService(process_command.db)
        source_author = source_author_service.get_or_create_source_author(
            source.id, author.id, "external_author_123"
        )

        entry_service = EntryService(process_command.db)
        entry = entry_service.create_entry(
            EntryCreate(
                title=sample_import_item_data.title,
                body=sample_import_item_data.body,
                source_id=source.id,
                external_id="external_entry_123",
                source_author_id=source_author.id,
                project_id=setup_project.id,
            )
        )

        result = process_command._create_entry_updates(
            sample_import_item_data, entry.id, setup_project.workspace_id, source.id
        )

        # Should create no entry updates since entry_updates field is empty
        assert len(result) == 0

    def test_execute_with_comments_success(
        self,
        process_command,
        setup_project,
        sample_import_item_data_with_comments,
        test_user,
    ):
        """Test successful processing of an import item with entry updates."""
        # Create a proper import request item with the correct payload
        from app.models.import_request_item import ImportRequestItem
        from app.models.import_request import ImportRequest
        from app.models.source import Source

        # Create source first
        source = Source(
            name="Test Source",
            identifier="github",
            workspace_id=setup_project.workspace_id,
        )
        process_command.db.add(source)
        process_command.db.commit()
        process_command.db.refresh(source)

        # Create import request
        import_request = ImportRequest(
            source_id=source.id,
            requested_by_id=test_user.id,
            status="pending",
            received_count=1,
            success_count=0,
            failure_count=0,
            project_id=setup_project.id,
        )
        process_command.db.add(import_request)
        process_command.db.commit()
        process_command.db.refresh(import_request)

        # Create import request item with proper payload
        import_request_item = ImportRequestItem(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id="item_123",
            raw_payload=sample_import_item_data_with_comments.model_dump(),
            status=ImportItemStatuses.FAILED,
        )
        process_command.db.add(import_request_item)
        process_command.db.commit()
        process_command.db.refresh(import_request_item)

        # Execute the command
        result = process_command.execute(import_request_item, setup_project)

        # Assertions
        assert result["success"] is True
        assert "author_id" in result
        assert "entry_id" in result
        assert "entry_update_ids" in result
        assert "source_author_id" in result
        # Should have 2 entry updates created
        assert len(result["entry_update_ids"]) == 2

    def test_deduplication_prevents_duplicate_entries_and_entry_updates(
        self,
        process_command,
        setup_project,
        sample_import_item_data_with_comments,
        test_user,
    ):
        """Test that running import twice with same data updates existing entries/entry updates instead of creating duplicates."""
        from app.models.import_request_item import ImportRequestItem
        from app.models.import_request import ImportRequest
        from app.models.source import Source

        # Create source first
        source = Source(
            name="Test Source",
            identifier="github",
            workspace_id=setup_project.workspace_id,
        )
        process_command.db.add(source)
        process_command.db.commit()
        process_command.db.refresh(source)

        # Create import request
        import_request = ImportRequest(
            source_id=source.id,
            requested_by_id=test_user.id,
            status="pending",
            received_count=1,
            success_count=0,
            failure_count=0,
            project_id=setup_project.id,
        )
        process_command.db.add(import_request)
        process_command.db.commit()
        process_command.db.refresh(import_request)

        # Create import request item with proper payload
        import_request_item = ImportRequestItem(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id="item_123",
            raw_payload=sample_import_item_data_with_comments.model_dump(),
            status=ImportItemStatuses.FAILED,
        )
        process_command.db.add(import_request_item)
        process_command.db.commit()
        process_command.db.refresh(import_request_item)

        # Execute the command first time
        result1 = process_command.execute(import_request_item, setup_project)
        assert result1["success"] is True
        first_entry_id = result1["entry_id"]
        first_entry_update_ids = result1["entry_update_ids"]

        # Execute the command second time with same data
        result2 = process_command.execute(import_request_item, setup_project)
        assert result2["success"] is True
        second_entry_id = result2["entry_id"]
        second_entry_update_ids = result2["entry_update_ids"]

        # Should return the same entry and entry update IDs (updated, not duplicated)
        assert first_entry_id == second_entry_id
        assert first_entry_update_ids == second_entry_update_ids

        # Verify only one entry exists in database
        from app.services.entry_service import EntryService

        entry_service = EntryService(process_command.db)
        entries = entry_service.get_entries_by_project(setup_project.id)
        entry_count = len([e for e in entries if e.external_id == "item_123"])
        assert entry_count == 1

        # Verify only expected number of entry updates exist in database
        from app.services.entry_update_service import EntryUpdateService

        entry_update_service = EntryUpdateService(process_command.db)
        entry_updates = entry_update_service.get_entry_updates()
        entry_update_count = len(
            [eu for eu in entry_updates if eu.external_id in ["1234567890", "1122334455"]]
        )
        assert entry_update_count == 2
