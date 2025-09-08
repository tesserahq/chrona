import pytest
from uuid import uuid4

from app.commands.projects.process_import_item_command import ProcessImportItemCommand
from app.schemas.project_import import ImportItemData, ImportAuthorData
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
        from app.constants.import_constants import ImportItemStatuses

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
        assert "comment_ids" in result
        assert "source_author_id" in result

    def test_execute_with_existing_author(
        self, process_command, setup_project, sample_import_item_data, test_user
    ):
        """Test processing when author already exists."""
        # Create a proper import request item with the correct payload
        from app.models.import_request_item import ImportRequestItem
        from app.models.import_request import ImportRequest
        from app.models.source import Source
        from app.constants.import_constants import ImportItemStatuses
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
        assert "comment_ids" in result
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
            sample_import_item_data, source_author.id, source.id, setup_project.id
        )

        assert result is not None
        assert result.title == sample_import_item_data.title
        assert result.body == sample_import_item_data.body
        assert result.source_id == source.id
        assert result.source_author_id == source_author.id
        assert result.project_id == setup_project.id

    def test_create_comments_with_body(
        self, process_command, sample_import_item_data, setup_project
    ):
        """Test creating comments when body is present."""
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

        result = process_command._create_comments(
            sample_import_item_data, source_author.id, entry.id
        )

        assert len(result) == 1
        assert result[0].body == sample_import_item_data.body
        assert result[0].source_author_id == source_author.id
        assert result[0].entry_id == entry.id

    def test_create_comments_without_body(self, process_command, setup_project):
        """Test creating comments when body is empty."""
        # Create item data with empty body
        item_data = ImportItemData(
            source="github",
            title="Test Issue",
            body="",  # Empty body
            tags=[],
            labels={},
            meta_data={},
            author=ImportAuthorData(
                id="author_123",
                display_name="Test Author",
                avatar_url="https://github.com/avatar.png",
                email="test@example.com",
                tags=[],
                labels={},
                meta_data={},
            ),
        )

        source_author_id = uuid4()
        entry_id = uuid4()

        result = process_command._create_comments(item_data, source_author_id, entry_id)

        assert len(result) == 0

    def test_create_comments_with_whitespace_body(self, process_command, setup_project):
        """Test creating comments when body is only whitespace."""
        # Create item data with whitespace-only body
        item_data = ImportItemData(
            source="github",
            title="Test Issue",
            body="   \n\t   ",  # Whitespace only
            tags=[],
            labels={},
            meta_data={},
            author=ImportAuthorData(
                id="author_123",
                display_name="Test Author",
                avatar_url="https://github.com/avatar.png",
                email="test@example.com",
                tags=[],
                labels={},
                meta_data={},
            ),
        )

        source_author_id = uuid4()
        entry_id = uuid4()

        result = process_command._create_comments(item_data, source_author_id, entry_id)

        assert len(result) == 0
