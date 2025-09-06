from uuid import uuid4

from app.schemas.entry import EntryCreate, EntryUpdate
from app.services.entry_service import EntryService


def test_create_entry(db, setup_source, setup_source_author, setup_project):
    service = EntryService(db)
    source = setup_source
    source_author = setup_source_author
    project = setup_project

    entry_data = EntryCreate(
        title="Test Entry",
        body="This is a test entry body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test", "example"],
        labels={"priority": "high"},
        meta_data={"created_by": "test"},
        source_author_id=source_author.id,
        project_id=project.id,
    )
    entry = service.create_entry(entry_data)
    assert entry.id is not None
    assert entry.title is not None
    assert entry.source_author_id is not None
    assert entry.project_id is not None
    assert "test" in entry.tags
    assert entry.labels["priority"] == "high"
    assert entry.meta_data["created_by"] == "test"


def test_get_entry(db, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    retrieved = service.get_entry(entry.id)
    assert retrieved is not None
    assert retrieved.id == entry.id


def test_get_entries(db, setup_entry):
    service = EntryService(db)
    entry = setup_entry
    entries = service.get_entries()
    assert isinstance(entries, list)
    assert len(entries) >= 1


def test_update_entry(db, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    update = EntryUpdate(title="Updated Title", body="Updated body")
    updated = service.update_entry(entry.id, update)

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.body == "Updated body"


def test_delete_entry(db, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    assert service.delete_entry(entry.id) is True
    assert service.get_entry(entry.id) is None


def test_search_entries(db, setup_entry):
    service = EntryService(db)
    entry = setup_entry

    # exact match by title
    results = service.search({"title": entry.title})
    assert len(results) == 1
    assert results[0].id == entry.id

    # ilike partial on title
    partial = entry.title[1 : len(entry.title) // 2]
    results = service.search({"title": {"operator": "ilike", "value": f"%{partial}%"}})
    assert len(results) >= 1

    # filter by source_author_id
    results = service.search({"source_author_id": entry.source_author_id})
    assert len(results) >= 1

    # filter by project_id
    results = service.search({"project_id": entry.project_id})
    assert len(results) >= 1

    # no match case
    results = service.search({"external_id": str(uuid4())})
    assert len(results) == 0
