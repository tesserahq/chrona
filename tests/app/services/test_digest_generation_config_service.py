import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from app.services.digest_generation_config_service import DigestGenerationConfigService
from app.schemas.digest_generation_config import (
    DigestGenerationConfigCreate,
    DigestGenerationConfigUpdate,
)
from app.exceptions.resource_not_found_error import ResourceNotFoundError
from app.constants.digest_constants import DigestStatuses


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
        "query": "Summarize the tasks and their latest updates.",
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
        "query": "Summarize the tasks and their latest updates.",
    }

    from app.models.digest_generation_config import DigestGenerationConfig

    digest_generation_config = DigestGenerationConfig(**digest_generation_config_data)
    db.add(digest_generation_config)
    db.commit()
    db.refresh(digest_generation_config)
    return digest_generation_config


@pytest.fixture
def setup_source_and_author(db, setup_workspace, faker):
    """Create a test source and source author for entries."""
    from app.models.source import Source
    from app.models.author import Author
    from app.models.source_author import SourceAuthor

    # Create source
    source_data = {
        "name": faker.company(),
        "description": faker.text(100),
        "identifier": str(faker.uuid4()),
        "workspace_id": setup_workspace.id,
    }
    source = Source(**source_data)
    db.add(source)
    db.commit()
    db.refresh(source)

    # Create author
    author_data = {
        "display_name": faker.name(),
        "avatar_url": faker.url(),
        "email": faker.email(),
        "tags": ["test"],
        "labels": {"type": "user"},
        "meta_data": {"source": "test"},
        "workspace_id": setup_workspace.id,
    }
    author = Author(**author_data)
    db.add(author)
    db.commit()
    db.refresh(author)

    # Create source_author relationship
    source_author_data = {
        "author_id": author.id,
        "source_id": source.id,
        "source_author_id": str(faker.uuid4()),
    }
    source_author = SourceAuthor(**source_author_data)
    db.add(source_author)
    db.commit()
    db.refresh(source_author)

    return source, author, source_author


@pytest.fixture
def setup_test_entries(db, setup_source_and_author, setup_project, faker):
    """Create test entries for today with matching tags and labels."""
    source, author, source_author = setup_source_and_author
    today = date.today()

    entries = []
    for i in range(3):
        entry_data = {
            "title": f"Test Entry {i}",
            "body": f"Test body content for entry {i}",
            "source_id": source.id,
            "external_id": f"ext-{i}",
            "tags": ["metal-api", "vmass"],
            "labels": {"hola": "chau"},
            "meta_data": {},
            "source_author_id": source_author.id,
            "project_id": setup_project.id,
            "created_at": datetime.combine(today, datetime.min.time()),
        }

        from app.models.entry import Entry

        entry = Entry(**entry_data)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        entries.append(entry)

    return entries


@pytest.fixture
def setup_test_entry_updates(db, setup_test_entries, setup_source_and_author, faker):
    """Create test entry updates for the test entries."""
    source, author, source_author = setup_source_and_author
    entries = setup_test_entries
    now = datetime.now()

    entry_updates = []
    for i, entry in enumerate(entries):
        update_data = {
            "body": f"Latest update for entry {i}",
            "source_author_id": source_author.id,
            "entry_id": entry.id,
            "tags": [],
            "labels": {},
            "meta_data": {},
            "external_id": f"update-{i}",
            "source_id": source.id,
            "source_created_at": now,  # Set to current time so it's within the last 2 days
        }

        from app.models.entry_update import EntryUpdate

        entry_update = EntryUpdate(**update_data)
        db.add(entry_update)
        db.commit()
        db.refresh(entry_update)
        entry_updates.append(entry_update)

    return entry_updates


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

    def test_generate_draft_digest(
        self,
        digest_generation_config_service,
        setup_digest_generation_config,
        setup_test_entries,
        setup_test_entry_updates,
    ):
        """Test generating a draft digest with matching entries."""
        config = setup_digest_generation_config
        entries = setup_test_entries
        entry_updates = setup_test_entry_updates

        # Generate the draft digest
        draft_digest = digest_generation_config_service.generate_draft_digest(config.id)

        # Verify the digest was created
        assert draft_digest is not None
        assert draft_digest.title == f"Draft Digest - {config.title}"
        assert draft_digest.status == DigestStatuses.DRAFT
        assert draft_digest.digest_generation_config_id == config.id
        assert draft_digest.project_id == config.project_id

        # Verify entries are included
        assert len(draft_digest.entries_ids) == len(entries)
        assert set(draft_digest.entries_ids) == {entry.id for entry in entries}

        # Verify entry updates are included
        assert len(draft_digest.entry_updates_ids) == len(entry_updates)
        assert set(draft_digest.entry_updates_ids) == {
            update.id for update in entry_updates
        }

        # Verify the digest body format
        assert "* Test Entry 0" in draft_digest.body
        assert "Test body content for entry 0" in draft_digest.body
        assert "Latest update: Latest update for entry 0" in draft_digest.body
        assert "* Test Entry 1" in draft_digest.body
        assert "* Test Entry 2" in draft_digest.body

        # Verify date range - should be within the last 2 days for daily cron
        today = date.today()
        yesterday = today - timedelta(days=1)

        # from_date should be either today or yesterday (depending on when the test runs vs cron schedule)
        # The cron runs at 10 AM UTC daily, so if we're before 10 AM, from_date would be yesterday
        assert draft_digest.from_date.date() in [today, yesterday]
        # to_date should be today (when the digest is being generated)
        assert draft_digest.to_date.date() == today

    def test_generate_draft_digest_no_matching_entries(
        self,
        digest_generation_config_service,
        setup_digest_generation_config,
    ):
        """Test generating a draft digest when no entries match the criteria."""
        config = setup_digest_generation_config
        # Update config to not generate empty digests
        config.generate_empty_digest = False
        digest_generation_config_service.db.commit()

        with pytest.raises(
            ResourceNotFoundError, match="No entries found matching the criteria"
        ):
            digest_generation_config_service.generate_draft_digest(config.id)

    def test_generate_draft_digest_empty_digest_allowed(
        self,
        digest_generation_config_service,
        setup_digest_generation_config,
    ):
        """Test generating a draft digest when no entries match but empty digest is allowed."""
        config = setup_digest_generation_config
        # Ensure empty digest is allowed
        config.generate_empty_digest = True
        digest_generation_config_service.db.commit()

        # Generate the draft digest
        draft_digest = digest_generation_config_service.generate_draft_digest(config.id)

        # Verify the digest was created even with no entries
        assert draft_digest is not None
        assert draft_digest.title == f"Draft Digest - {config.title}"
        assert draft_digest.status == DigestStatuses.DRAFT
        assert len(draft_digest.entries_ids) == 0
        assert len(draft_digest.entry_updates_ids) == 0
        assert draft_digest.body == ""

    def test_generate_draft_digest_config_not_found(
        self,
        digest_generation_config_service,
    ):
        """Test generating a draft digest with non-existent config."""
        with pytest.raises(
            ResourceNotFoundError, match="Digest generation config with ID"
        ):
            digest_generation_config_service.generate_draft_digest(uuid4())
