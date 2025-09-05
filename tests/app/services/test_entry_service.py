from uuid import uuid4
from sqlalchemy.orm import Session

from app.schemas.entry import EntryUpdate
from app.services.entry_service import EntryService


def test_create_entry(db: Session, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    assert entry.id is not None
    assert entry.title is not None
    assert entry.author_id is not None
    assert entry.project_id is not None
    assert "notes" in entry.tags
    assert entry.labels["priority"] == "high"
    assert entry.meta_data["ingested_by"] == "test"


def test_get_entry(db: Session, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    retrieved = service.get_entry(entry.id)
    assert retrieved is not None
    assert retrieved.id == entry.id


def test_get_entries(db: Session, setup_entry):
    service = EntryService(db)
    entry = setup_entry
    entries = service.get_entries()
    assert isinstance(entries, list)
    assert len(entries) >= 1


def test_update_entry(db: Session, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    update = EntryUpdate(title="Updated Title", body="Updated body")
    updated = service.update_entry(entry.id, update)

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.body == "Updated body"


def test_delete_entry(db: Session, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    assert service.delete_entry(entry.id) is True
    assert service.get_entry(entry.id) is None


def test_search_entries(db: Session, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    # exact match by title
    results = service.search({"title": entry.title})
    assert len(results) == 1
    assert results[0].id == entry.id

    # ilike partial on title
    partial = entry.title[: max(1, len(entry.title) // 2)]
    results = service.search({"title": {"operator": "ilike", "value": f"%{partial}%"}})
    assert len(results) >= 1

    # filter by author_id
    results = service.search({"author_id": entry.author_id})
    assert len(results) >= 1

    # filter by project_id
    results = service.search({"project_id": entry.project_id})
    assert len(results) >= 1

    # no match case
    results = service.search({"external_id": str(uuid4())})
    assert len(results) == 0
