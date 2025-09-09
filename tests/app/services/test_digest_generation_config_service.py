import pytest
from uuid import uuid4
from app.services.digest_generation_config_service import DigestGenerationConfigService
from app.schemas.digest_generation_config import (
    DigestGenerationConfigCreate,
    DigestGenerationConfigUpdate,
)
from app.exceptions.resource_not_found_error import ResourceNotFoundError


@pytest.fixture
def digest_generation_config_service(db):
    """Create a DigestGenerationConfigService instance for testing."""
    return DigestGenerationConfigService(db)


@pytest.fixture
def sample_digest_generation_config_data(faker):
    """Sample data for creating a digest generation config."""
    return {
        "title": faker.sentence(nb_words=3),
        "filter_tags": ["metal-api", "vmass"],
        "filter_labels": {"hola": "chau"},
        "tags": ["emapi", "daily"],
        "labels": {"otro": "aca"},
        "system_prompt": faker.text(200),
        "timezone": "UTC",
        "generate_empty_digest": True,
        "cron_expression": "0 10 * * *",
    }


@pytest.fixture
def setup_digest_generation_config(db, setup_project, faker):
    """Create a test digest generation config in the database."""
    project = setup_project

    digest_generation_config_data = {
        "title": faker.sentence(nb_words=3),
        "filter_tags": ["metal-api", "vmass"],
        "filter_labels": {"hola": "chau"},
        "tags": ["emapi", "daily"],
        "labels": {"otro": "aca"},
        "system_prompt": faker.text(200),
        "timezone": "UTC",
        "generate_empty_digest": True,
        "cron_expression": "0 10 * * *",
        "project_id": project.id,
    }

    from app.models.digest_generation_config import DigestGenerationConfig

    digest_generation_config = DigestGenerationConfig(**digest_generation_config_data)
    db.add(digest_generation_config)
    db.commit()
    db.refresh(digest_generation_config)
    return digest_generation_config


class TestDigestGenerationConfigService:
    """Test cases for DigestGenerationConfigService."""

    def test_get_digest_generation_config(self, db, setup_digest_generation_config):
        """Test getting a digest generation config by ID."""
        service = DigestGenerationConfigService(db)
        result = service.get_digest_generation_config(setup_digest_generation_config.id)

        assert result is not None
        assert result.id == setup_digest_generation_config.id
        assert result.title == setup_digest_generation_config.title

    def test_get_digest_generation_config_not_found(
        self, digest_generation_config_service
    ):
        """Test getting a non-existent digest generation config."""
        result = digest_generation_config_service.get_digest_generation_config(uuid4())
        assert result is None

    def test_get_digest_generation_configs(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test getting all digest generation configs."""
        # Create multiple digest generation configs
        for i in range(3):
            data = sample_digest_generation_config_data.copy()
            data["title"] = f"Test Digest {i}"
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**data), setup_project.id
            )

        result = digest_generation_config_service.get_digest_generation_configs()
        assert len(result) >= 3

    def test_get_digest_generation_configs_pagination(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test pagination for getting digest generation configs."""
        # Create 5 digest generation configs
        for i in range(5):
            data = sample_digest_generation_config_data.copy()
            data["title"] = f"Test Digest {i}"
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**data), setup_project.id
            )

        # Test pagination
        result = digest_generation_config_service.get_digest_generation_configs(
            skip=2, limit=2
        )
        assert len(result) == 2

    def test_get_digest_generation_configs_by_project(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test getting digest generation configs by project."""
        another_project = setup_project
        # Create digest generation configs for both projects
        for i, proj in enumerate([setup_project, another_project]):
            data = sample_digest_generation_config_data.copy()
            data["title"] = f"Test Digest {i}"
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**data), proj.id
            )

        # Get digest generation configs for project 1
        result = (
            digest_generation_config_service.get_digest_generation_configs_by_project(
                setup_project.id
            )
        )
        assert len(result) >= 1
        assert all(config.project_id == setup_project.id for config in result)

    def test_create_digest_generation_config(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test creating a digest generation config."""
        digest_generation_config = (
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**sample_digest_generation_config_data),
                setup_project.id,
            )
        )

        assert digest_generation_config.id is not None
        assert (
            digest_generation_config.title
            == sample_digest_generation_config_data["title"]
        )
        assert digest_generation_config.project_id == setup_project.id
        assert (
            digest_generation_config.system_prompt
            == sample_digest_generation_config_data["system_prompt"]
        )

    def test_create_digest_generation_config_invalid_project(
        self, digest_generation_config_service, sample_digest_generation_config_data
    ):
        """Test creating a digest generation config with invalid project."""
        digest_generation_config_in = DigestGenerationConfigCreate(
            **sample_digest_generation_config_data
        )
        service = digest_generation_config_service

        with pytest.raises(ResourceNotFoundError):
            service.create_digest_generation_config(
                digest_generation_config_in, uuid4()
            )

    def test_update_digest_generation_config(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test updating a digest generation config."""
        digest_generation_config = (
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**sample_digest_generation_config_data),
                setup_project.id,
            )
        )

        update_data = {"title": "Updated Title"}
        updated = digest_generation_config_service.update_digest_generation_config(
            digest_generation_config.id, DigestGenerationConfigUpdate(**update_data)
        )

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.id == digest_generation_config.id

    def test_update_digest_generation_config_not_found(
        self, digest_generation_config_service
    ):
        """Test updating a non-existent digest generation config."""
        update_data = {"title": "Updated Title"}
        result = digest_generation_config_service.update_digest_generation_config(
            uuid4(), DigestGenerationConfigUpdate(**update_data)
        )
        assert result is None

    def test_delete_digest_generation_config(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test soft deleting a digest generation config."""
        digest_generation_config = (
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**sample_digest_generation_config_data),
                setup_project.id,
            )
        )

        success = digest_generation_config_service.delete_digest_generation_config(
            digest_generation_config.id
        )
        assert success is True

        # Verify it's soft deleted
        deleted_definition = (
            digest_generation_config_service.get_digest_generation_config(
                digest_generation_config.id
            )
        )
        assert deleted_definition is None

    def test_delete_digest_generation_config_not_found(
        self, digest_generation_config_service
    ):
        """Test deleting a non-existent digest generation config."""
        success = digest_generation_config_service.delete_digest_generation_config(
            uuid4()
        )
        assert success is False

    def test_search_digest_generation_configs(
        self,
        digest_generation_config_service,
        sample_digest_generation_config_data,
        setup_project,
    ):
        """Test searching digest generation configs with filters."""
        # Create digest generation configs with different titles
        for i in range(3):
            data = sample_digest_generation_config_data.copy()
            data["title"] = f"Test Digest {i}"
            digest_generation_config_service.create_digest_generation_config(
                DigestGenerationConfigCreate(**data), setup_project.id
            )

        # Search by title
        result = digest_generation_config_service.search_digest_generation_configs(
            {"title": "Test Digest 1"}
        )
        assert len(result) == 1
        assert result[0].title == "Test Digest 1"
