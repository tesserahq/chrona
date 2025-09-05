import pytest
from app.models.entry import Entry


@pytest.fixture
def setup_entry(db, setup_source_author, setup_project, setup_source, faker):
    """Create a test entry in the database with optional overrides."""
    source_author = setup_source_author
    project = setup_project
    source = setup_source

    entry_data = {
        "title": faker.sentence(nb_words=6),
        "body": faker.text(200),
        "source_id": source.id,
        "external_id": str(faker.uuid4()),
        "tags": ["notes"],
        "labels": {"priority": "high"},
        "meta_data": {"created_by": "test"},
        "source_author_id": source_author.id,
        "project_id": project.id,
    }

    entry = Entry(**entry_data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
