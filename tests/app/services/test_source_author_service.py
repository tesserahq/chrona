import pytest
from uuid import uuid4

from app.services.source_author_service import SourceAuthorService
from app.models.source_author import SourceAuthor
from app.schemas.source_author import SourceAuthorCreate, SourceAuthorUpdate


@pytest.fixture
def source_author_service(db):
    """Create a SourceAuthorService instance for testing."""
    return SourceAuthorService(db)


class TestSourceAuthorService:
    """Test cases for SourceAuthorService."""

    def test_get_source_author_success(
        self, source_author_service, setup_source_author
    ):
        """Test getting a source author by ID."""
        result = source_author_service.get_source_author(setup_source_author.id)

        assert result is not None
        assert result.id == setup_source_author.id
        assert result.author_id == setup_source_author.author_id
        assert result.source_id == setup_source_author.source_id
        assert result.source_author_id == setup_source_author.source_author_id

    def test_get_source_author_not_found(self, source_author_service):
        """Test getting a source author that doesn't exist."""
        result = source_author_service.get_source_author(uuid4())

        assert result is None

    def test_get_source_authors(self, source_author_service, setup_source_author):
        """Test getting a list of source authors."""
        result = source_author_service.get_source_authors(skip=0, limit=10)

        assert len(result) >= 1
        # Check that our created source author is in the results
        source_author_ids = [sa.id for sa in result]
        assert setup_source_author.id in source_author_ids

    def test_get_source_authors_by_source(
        self, source_author_service, setup_source_author
    ):
        """Test getting source authors by source ID."""
        result = source_author_service.get_source_authors_by_source(
            setup_source_author.source_id
        )

        assert len(result) >= 1
        # Check that our created source author is in the results
        source_author_ids = [sa.id for sa in result]
        assert setup_source_author.id in source_author_ids
        # Verify all results are for the correct source
        for sa in result:
            assert sa.source_id == setup_source_author.source_id

    def test_get_source_author_by_external_id_success(
        self, source_author_service, setup_source_author
    ):
        """Test getting a source author by external ID."""
        result = source_author_service.get_source_author_by_external_id(
            setup_source_author.source_id, setup_source_author.source_author_id
        )

        assert result is not None
        assert result.id == setup_source_author.id
        assert result.source_id == setup_source_author.source_id
        assert result.source_author_id == setup_source_author.source_author_id

    def test_get_source_author_by_external_id_not_found(
        self, source_author_service, setup_source
    ):
        """Test getting a source author by external ID that doesn't exist."""
        result = source_author_service.get_source_author_by_external_id(
            setup_source.id, "nonexistent"
        )

        assert result is None

    def test_create_source_author(
        self, source_author_service, setup_author, setup_source
    ):
        """Test creating a new source author."""
        source_author_data = SourceAuthorCreate(
            author_id=setup_author.id,
            source_id=setup_source.id,
            source_author_id="test_external_id",
        )

        result = source_author_service.create_source_author(source_author_data)

        assert result is not None
        assert result.author_id == setup_author.id
        assert result.source_id == setup_source.id
        assert result.source_author_id == "test_external_id"

    def test_get_or_create_source_author_existing(
        self, source_author_service, setup_source_author
    ):
        """Test get_or_create when source author already exists."""
        result = source_author_service.get_or_create_source_author(
            setup_source_author.source_id,
            setup_source_author.author_id,
            setup_source_author.source_author_id,
        )

        assert result is not None
        assert result.id == setup_source_author.id
        assert result.source_id == setup_source_author.source_id
        assert result.author_id == setup_source_author.author_id
        assert result.source_author_id == setup_source_author.source_author_id

    def test_get_or_create_source_author_new(
        self, source_author_service, setup_author, setup_source
    ):
        """Test get_or_create when source author doesn't exist."""
        result = source_author_service.get_or_create_source_author(
            setup_source.id, setup_author.id, "new_external_id"
        )

        assert result is not None
        assert result.source_id == setup_source.id
        assert result.author_id == setup_author.id
        assert result.source_author_id == "new_external_id"

    def test_update_source_author_success(
        self, source_author_service, setup_source_author, setup_author
    ):
        """Test updating an existing source author."""
        new_author_id = setup_author.id
        update_data = SourceAuthorUpdate(author_id=new_author_id)

        result = source_author_service.update_source_author(
            setup_source_author.id, update_data
        )

        assert result is not None
        assert result.id == setup_source_author.id
        assert result.author_id == new_author_id
        assert result.source_id == setup_source_author.source_id
        assert result.source_author_id == setup_source_author.source_author_id

    def test_update_source_author_not_found(self, source_author_service):
        """Test updating a source author that doesn't exist."""
        update_data = SourceAuthorUpdate(author_id=uuid4())
        result = source_author_service.update_source_author(uuid4(), update_data)

        assert result is None

    def test_delete_source_author(self, source_author_service, setup_source_author):
        """Test deleting a source author."""
        result = source_author_service.delete_source_author(setup_source_author.id)

        assert result is True

        # Verify the source author was actually deleted
        deleted_source_author = source_author_service.get_source_author(
            setup_source_author.id
        )
        assert deleted_source_author is None

    def test_search(self, source_author_service, setup_source_author):
        """Test searching source authors."""
        filters = {"author_id": setup_source_author.author_id}
        result = source_author_service.search(filters)

        assert len(result) >= 1
        # Check that our created source author is in the results
        source_author_ids = [sa.id for sa in result]
        assert setup_source_author.id in source_author_ids

    def test_get_source_authors_pagination(
        self, source_author_service, setup_source_author
    ):
        """Test getting source authors with pagination."""
        result = source_author_service.get_source_authors(skip=0, limit=1)

        assert len(result) <= 1
        # If we have results, verify they are SourceAuthor objects
        if result:
            assert hasattr(result[0], "id")
            assert hasattr(result[0], "author_id")
            assert hasattr(result[0], "source_id")

    def test_get_source_authors_by_source_pagination(
        self, source_author_service, setup_source_author
    ):
        """Test getting source authors by source with pagination."""
        result = source_author_service.get_source_authors_by_source(
            setup_source_author.source_id, skip=0, limit=1
        )

        assert len(result) <= 1
        # If we have results, verify they are for the correct source
        if result:
            assert result[0].source_id == setup_source_author.source_id
