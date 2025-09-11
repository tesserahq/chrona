import pytest
from app.models.entry_update import EntryUpdate


@pytest.fixture
def setup_entry_update(db, setup_source_author, setup_entry, setup_source, faker):
    """Create a test entry update in the database with optional overrides."""
    source_author = setup_source_author
    entry = setup_entry
    source = setup_source

    entry_update_data = {
        "body": faker.text(200),
        "source_author_id": source_author.id,
        "entry_id": entry.id,
        "tags": ["feedback"],
        "labels": {"priority": "medium"},
        "meta_data": {"source": "test"},
        "external_id": faker.uuid4(),
        "source_id": source.id,
    }

    entry_update = EntryUpdate(**entry_update_data)
    db.add(entry_update)
    db.commit()
    db.refresh(entry_update)
    return entry_update
