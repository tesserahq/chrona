import pytest
from uuid import uuid4

from app.services.author_service import AuthorService
from app.models.author import Author
from app.models.source_author import SourceAuthor
from app.schemas.author import AuthorCreate, AuthorUpdate


@pytest.fixture
def author_service(db):
    """Create an AuthorService instance for testing."""
    return AuthorService(db)


@pytest.fixture
def setup_multiple_authors(db, setup_workspace, faker):
    """Create multiple test authors in the same workspace."""
    authors = []

    for i in range(3):
        author_data = {
            "display_name": f"{faker.name()} {i}",
            "avatar_url": faker.url(),
            "email": faker.email(),
            "tags": ["test", f"author_{i}"],
            "labels": {"type": "user", "index": i},
            "meta_data": {"source": "test", "created_for": "merge_test"},
            "workspace_id": setup_workspace.id,
        }

        author = Author(**author_data)
        db.add(author)
        authors.append(author)

    db.commit()
    for author in authors:
        db.refresh(author)

    return authors


@pytest.fixture
def setup_authors_with_source_authors(db, setup_multiple_authors, setup_source, faker):
    """Create source_author relationships for the test authors."""
    source_authors = []

    for i, author in enumerate(setup_multiple_authors):
        source_author_data = {
            "author_id": author.id,
            "source_id": setup_source.id,
            "source_author_id": f"external_id_{i}",
        }

        source_author = SourceAuthor(**source_author_data)
        db.add(source_author)
        source_authors.append(source_author)

    db.commit()
    for source_author in source_authors:
        db.refresh(source_author)

    return setup_multiple_authors, source_authors


class TestAuthorService:
    """Test cases for AuthorService."""

    def test_get_author_success(self, author_service, setup_author):
        """Test getting an author by ID."""
        result = author_service.get_author(setup_author.id)

        assert result is not None
        assert result.id == setup_author.id
        assert result.display_name == setup_author.display_name
        assert result.email == setup_author.email

    def test_get_author_not_found(self, author_service):
        """Test getting an author that doesn't exist."""
        result = author_service.get_author(uuid4())

        assert result is None

    def test_create_author(self, author_service, setup_workspace, faker):
        """Test creating a new author."""
        author_data = AuthorCreate(
            display_name=faker.name(),
            avatar_url=faker.url(),
            email=faker.email(),
            tags=["new", "test"],
            labels={"type": "contributor"},
            meta_data={"source": "api"},
        )

        result = author_service.create_author(author_data, setup_workspace.id)

        assert result is not None
        assert result.display_name == author_data.display_name
        assert result.email == author_data.email
        assert result.workspace_id == setup_workspace.id
        assert result.tags == ["new", "test"]
        assert result.labels == {"type": "contributor"}

    def test_update_author(self, author_service, setup_author, faker):
        """Test updating an existing author."""
        new_name = faker.name()
        update_data = AuthorUpdate(display_name=new_name)

        result = author_service.update_author(setup_author.id, update_data)

        assert result is not None
        assert result.display_name == new_name
        assert result.email == setup_author.email  # Should remain unchanged

    def test_delete_author(self, author_service, setup_author):
        """Test soft deleting an author."""
        result = author_service.delete_author(setup_author.id)

        assert result is True

        # Verify author is soft deleted
        deleted_author = author_service.get_author(setup_author.id)
        assert deleted_author is None

    def test_merge_authors_success(
        self, author_service, setup_authors_with_source_authors
    ):
        """Test successfully merging multiple authors."""
        authors, source_authors = setup_authors_with_source_authors

        # Take the first author as merge target, others as sources
        merge_to_author = authors[0]
        authors_to_merge = authors[1:]
        author_ids_to_merge = [author.id for author in authors_to_merge]

        # Verify initial state
        assert len(source_authors) == 3
        initial_source_author_count = len(
            [sa for sa in source_authors if sa.author_id == merge_to_author.id]
        )
        assert initial_source_author_count == 1

        # Perform merge
        result = author_service.merge_authors(author_ids_to_merge, merge_to_author.id)

        assert result is True

        # Verify source_authors were updated
        from app.models.source_author import SourceAuthor

        remaining_source_authors = (
            author_service.db.query(SourceAuthor)
            .filter(SourceAuthor.author_id == merge_to_author.id)
            .all()
        )

        # Should now have all 3 source_authors pointing to merge_to_author
        assert len(remaining_source_authors) == 3

        # Verify old authors are soft deleted
        for author_id in author_ids_to_merge:
            deleted_author = author_service.get_author(author_id)
            assert deleted_author is None

    def test_merge_authors_target_not_found(
        self, author_service, setup_multiple_authors
    ):
        """Test merging when target author doesn't exist."""
        authors = setup_multiple_authors
        author_ids_to_merge = [authors[0].id]
        fake_target_id = uuid4()

        with pytest.raises(ValueError, match="Target author with ID .* not found"):
            author_service.merge_authors(author_ids_to_merge, fake_target_id)

    def test_merge_authors_source_not_found(
        self, author_service, setup_multiple_authors
    ):
        """Test merging when one of the source authors doesn't exist."""
        authors = setup_multiple_authors
        merge_to_author = authors[0]
        fake_author_id = uuid4()
        author_ids_to_merge = [fake_author_id]

        with pytest.raises(ValueError, match="Author with ID .* not found"):
            author_service.merge_authors(author_ids_to_merge, merge_to_author.id)

    def test_merge_authors_different_workspace(
        self, author_service, setup_multiple_authors, setup_workspace, faker, db
    ):
        """Test merging authors from different workspaces should fail."""
        authors = setup_multiple_authors
        merge_to_author = authors[0]

        # Create an author in a different workspace
        from app.models.workspace import Workspace

        different_workspace = Workspace(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=setup_workspace.created_by_id,
        )
        db.add(different_workspace)
        db.commit()
        db.refresh(different_workspace)

        different_author = Author(
            display_name=faker.name(),
            avatar_url=faker.url(),
            email=faker.email(),
            tags=["test"],
            labels={"type": "user"},
            meta_data={"source": "test"},
            workspace_id=different_workspace.id,
        )
        db.add(different_author)
        db.commit()
        db.refresh(different_author)

        with pytest.raises(
            ValueError, match="belongs to different workspace than target author"
        ):
            author_service.merge_authors([different_author.id], merge_to_author.id)

    def test_merge_authors_empty_list(self, author_service, setup_author):
        """Test merging with empty author list should fail."""
        with pytest.raises(
            ValueError, match="At least one author ID must be provided to merge"
        ):
            author_service.merge_authors([], setup_author.id)

    def test_merge_authors_target_in_source_list(
        self, author_service, setup_multiple_authors
    ):
        """Test merging when target author is in the source list should fail."""
        authors = setup_multiple_authors
        merge_to_author = authors[0]

        with pytest.raises(
            ValueError,
            match="merge_to_author_id cannot be in the list of authors to merge",
        ):
            author_service.merge_authors([merge_to_author.id], merge_to_author.id)

    def test_merge_authors_with_multiple_sources(
        self, author_service, setup_multiple_authors, setup_source, db, faker
    ):
        """Test merging authors that have source_authors from different sources."""
        authors = setup_multiple_authors

        # Create a second source
        from app.models.source import Source

        second_source = Source(
            name=faker.company(),
            description=faker.text(100),
            identifier=f"source_{faker.uuid4()}",
            workspace_id=authors[0].workspace_id,
        )
        db.add(second_source)
        db.commit()
        db.refresh(second_source)

        # Create source_authors for different sources
        source_authors = []
        for i, author in enumerate(authors):
            # Each author has source_authors from both sources
            for j, source in enumerate([setup_source, second_source]):
                source_author = SourceAuthor(
                    author_id=author.id,
                    source_id=source.id,
                    source_author_id=f"external_id_{i}_source_{j}",
                )
                db.add(source_author)
                source_authors.append(source_author)

        db.commit()
        for sa in source_authors:
            db.refresh(sa)

        merge_to_author = authors[0]
        authors_to_merge = authors[1:]
        author_ids_to_merge = [author.id for author in authors_to_merge]

        # Perform merge
        result = author_service.merge_authors(author_ids_to_merge, merge_to_author.id)

        assert result is True

        # Verify all source_authors now point to merge_to_author
        remaining_source_authors = (
            db.query(SourceAuthor)
            .filter(SourceAuthor.author_id == merge_to_author.id)
            .all()
        )

        # Should have 6 source_authors total (3 authors × 2 sources each)
        assert len(remaining_source_authors) == 6
