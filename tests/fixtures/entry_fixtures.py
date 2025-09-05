import pytest
from app.models.entry import Entry
from sqlalchemy.orm import Session


@pytest.fixture
def setup_entry(db: Session, setup_user, setup_project, faker):
    """Create a test entry in the database with optional overrides."""
    user = setup_user
    project = setup_project

    entry_data = {
        "title": faker.sentence(nb_words=6),
        "body": faker.text(200),
        "source": "import",
        "external_id": faker.uuid4(),
        "tags": ["notes"],
        "labels": {"priority": "high"},
        "meta_data": {"ingested_by": "test"},
        "author_id": user.id,
        "project_id": project.id,
    }

    entry = Entry(**entry_data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
