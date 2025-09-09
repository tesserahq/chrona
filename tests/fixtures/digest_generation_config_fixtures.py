import pytest
from uuid import uuid4
from app.models.digest_generation_config import DigestGenerationConfig


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

    digest_generation_config = DigestGenerationConfig(**digest_generation_config_data)
    db.add(digest_generation_config)
    db.commit()
    db.refresh(digest_generation_config)
    return digest_generation_config
