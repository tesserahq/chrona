import pytest
from uuid import uuid4
from app.services.digest_service import DigestService
from app.schemas.digest import DigestCreate, DigestUpdate
from app.exceptions.resource_not_found_error import ResourceNotFoundError


@pytest.fixture
def digest_service(db):
    """Create a DigestService instance for testing."""
    return DigestService(db)


class TestDigestService:
    """Test cases for DigestService."""

    def test_get_digest(self, db, setup_digest):
        """Test getting a single digest by ID."""
        service = DigestService(db)
        result = service.get_digest(setup_digest.id)

        assert result is not None
        assert result.id == setup_digest.id
        assert result.title == setup_digest.title
        assert result.body == setup_digest.body
        assert result.project_id == setup_digest.project_id
        assert (
            result.digest_generation_config_id
            == setup_digest.digest_generation_config_id
        )

    def test_get_digest_not_found(self, digest_service):
        """Test getting a non-existent digest."""
        result = digest_service.get_digest(uuid4())
        assert result is None

    def test_get_digests(self, db, setup_digest, setup_another_digest):
        """Test getting a list of digests."""
        service = DigestService(db)
        results = service.get_digests()

        assert len(results) >= 2
        ids = [r.id for r in results]
        assert setup_digest.id in ids
        assert setup_another_digest.id in ids

    def test_get_digests_pagination(self, db, setup_digest, setup_another_digest):
        """Test pagination for getting digests."""
        service = DigestService(db)

        # Test first page
        results = service.get_digests(skip=0, limit=1)
        assert len(results) == 1

        # Test second page
        results = service.get_digests(skip=1, limit=1)
        assert len(results) == 1

    def test_get_digests_by_project(
        self, db, setup_digest, setup_another_digest, setup_project
    ):
        """Test getting digests by project ID."""
        service = DigestService(db)
        project = setup_project

        results = service.get_digests_by_project(project.id)

        assert len(results) >= 2
        for digest in results:
            assert digest.project_id == project.id

    def test_get_digests_by_config(
        self, db, setup_digest, setup_another_digest, setup_digest_generation_config
    ):
        """Test getting digests by digest generation config ID."""
        service = DigestService(db)
        config = setup_digest_generation_config

        results = service.get_digests_by_config(config.id)

        assert len(results) >= 2
        for digest in results:
            assert digest.digest_generation_config_id == config.id

    def test_create_digest(
        self,
        digest_service,
        setup_project,
        setup_digest_generation_config,
        sample_digest_data,
    ):
        """Test creating a new digest."""
        project = setup_project
        config = setup_digest_generation_config

        digest_data = sample_digest_data.copy()
        digest_data["digest_generation_config_id"] = config.id
        digest_data["project_id"] = project.id

        digest_create = DigestCreate(**digest_data)
        result = digest_service.create_digest(digest_create)

        assert result.id is not None
        assert result.title == digest_data["title"]
        assert result.body == digest_data["body"]
        assert result.project_id == project.id
        assert result.digest_generation_config_id == config.id
        assert result.entries_ids == digest_data["entries_ids"]
        assert result.tags == digest_data["tags"]
        assert result.labels == digest_data["labels"]
        assert result.comments_ids == digest_data["comments_ids"]

    def test_create_digest_project_not_found(
        self, digest_service, setup_digest_generation_config, sample_digest_data
    ):
        """Test creating a digest with non-existent project ID."""
        config = setup_digest_generation_config

        digest_data = sample_digest_data.copy()
        digest_data["digest_generation_config_id"] = config.id
        digest_data["project_id"] = uuid4()  # Non-existent project ID

        digest_create = DigestCreate(**digest_data)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            digest_service.create_digest(digest_create)

        assert "Project with ID" in str(exc_info.value)

    def test_update_digest(self, digest_service, setup_digest):
        """Test updating an existing digest."""
        digest = setup_digest
        new_title = "Updated Digest Title"
        new_body = "Updated digest body content"

        update_data = DigestUpdate(
            title=new_title, body=new_body, tags=["updated", "modified"]
        )

        result = digest_service.update_digest(digest.id, update_data)

        assert result is not None
        assert result.id == digest.id
        assert result.title == new_title
        assert result.body == new_body
        assert "updated" in result.tags
        assert "modified" in result.tags

    def test_update_digest_not_found(self, digest_service):
        """Test updating a non-existent digest."""
        update_data = DigestUpdate(title="New Title")

        result = digest_service.update_digest(uuid4(), update_data)
        assert result is None

    def test_delete_digest(self, digest_service, setup_digest):
        """Test soft deleting a digest."""
        digest = setup_digest
        result = digest_service.delete_digest(digest.id)

        assert result is True

        # Verify digest is soft deleted
        deleted_digest = digest_service.get_digest(digest.id)
        assert deleted_digest is None

    def test_delete_digest_not_found(self, digest_service):
        """Test deleting a non-existent digest."""
        result = digest_service.delete_digest(uuid4())
        assert result is False

    def test_get_digests_with_filters(
        self, digest_service, setup_digest, setup_another_digest
    ):
        """Test getting digests with filters applied."""
        # Test simple equality filter on title
        results = digest_service.get_digests_with_filters(
            filters={"title": setup_digest.title}
        )

        assert len(results) >= 1
        for digest in results:
            assert digest.title == setup_digest.title

        # Test filtering by project_id
        results = digest_service.get_digests_with_filters(
            filters={"project_id": setup_digest.project_id}
        )

        assert len(results) >= 2  # Should find both digests

    def test_digest_relationships(self, db, setup_digest):
        """Test that digest relationships are properly loaded."""
        service = DigestService(db)
        digest = service.get_digest(setup_digest.id)

        assert digest is not None
        assert digest.project is not None
        assert digest.digest_generation_config is not None
        assert digest.project.id == setup_digest.project_id
        assert (
            digest.digest_generation_config.id
            == setup_digest.digest_generation_config_id
        )
