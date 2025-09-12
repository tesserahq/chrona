import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.models.digest import Digest


@pytest.fixture
def sample_digest_data(faker):
    """Sample data for creating a digest."""
    return {
        "title": faker.sentence(nb_words=4),
        "body": faker.text(500),
        "entries_ids": [uuid4(), uuid4()],
        "tags": ["daily", "summary"],
        "labels": {"priority": "high", "category": "news"},
        "entry_updates_ids": [uuid4()],
        "from_date": datetime.now(timezone.utc),
        "to_date": datetime.now(timezone.utc),
    }


@pytest.fixture
def setup_digest(db, setup_project, setup_digest_generation_config, faker):
    """Create a test digest in the database."""
    project = setup_project
    digest_generation_config = setup_digest_generation_config

    digest_data = {
        "title": faker.sentence(nb_words=4),
        "body": faker.text(500),
        "entries_ids": [uuid4(), uuid4()],
        "tags": ["daily", "summary"],
        "labels": {"priority": "high", "category": "news"},
        "entry_updates_ids": [uuid4()],
        "from_date": datetime.now(timezone.utc),
        "to_date": datetime.now(timezone.utc),
        "digest_generation_config_id": digest_generation_config.id,
        "project_id": project.id,
    }

    digest = Digest(**digest_data)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest


@pytest.fixture
def setup_another_digest(db, setup_project, setup_digest_generation_config, faker):
    """Create another test digest in the database."""
    project = setup_project
    digest_generation_config = setup_digest_generation_config

    digest_data = {
        "title": faker.sentence(nb_words=4),
        "body": faker.text(300),
        "entries_ids": [uuid4()],
        "tags": ["weekly", "report"],
        "labels": {"priority": "medium", "category": "analysis"},
        "entry_updates_ids": [],
        "from_date": datetime.now(timezone.utc),
        "to_date": datetime.now(timezone.utc),
        "digest_generation_config_id": digest_generation_config.id,
        "project_id": project.id,
    }

    digest = Digest(**digest_data)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest
