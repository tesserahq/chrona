from uuid import uuid4

from app.schemas.entry_update import EntryUpdateCreate, EntryUpdateUpdate
from app.services.entry_update_service import EntryUpdateService


def test_create_entry_update(db, setup_source_author, setup_entry, setup_source):
    service = EntryUpdateService(db)
    source_author = setup_source_author
    entry = setup_entry
    source = setup_source

    entry_update = EntryUpdateCreate(
        body="This is a test entry update",
        source_author_id=str(source_author.id),
        entry_id=str(entry.id),
        tags=["feedback"],
        labels={"priority": "medium"},
        meta_data={"source": "test"},
        external_id="test_external_id_123",
        source_id=str(source.id),
    )

    entry_update = service.create_entry_update(entry_update)

    assert entry_update.id is not None
    assert entry_update.body is not None
    assert entry_update.source_author_id is not None
    assert entry_update.entry_id is not None
    assert "feedback" in entry_update.tags
    assert entry_update.labels["priority"] == "medium"
    assert entry_update.meta_data["source"] == "test"


def test_get_entry_update(db, setup_entry_update):
    service = EntryUpdateService(db)
    entry_update = setup_entry_update

    retrieved = service.get_entry_update(entry_update.id)
    assert retrieved is not None
    assert retrieved.id == entry_update.id


def test_get_entry_updates(db, setup_entry_update):
    service = EntryUpdateService(db)
    entry_update = setup_entry_update
    entry_updates = service.get_entry_updates()
    assert isinstance(entry_updates, list)
    assert len(entry_updates) >= 1


def test_update_entry_update(db, setup_entry_update):
    service = EntryUpdateService(db)
    entry_update = setup_entry_update

    update = EntryUpdateUpdate(body="Updated entry update body", tags=["updated"])
    updated = service.update_entry_update(entry_update.id, update)

    assert updated is not None
    assert updated.body == "Updated entry update body"
    assert "updated" in updated.tags


def test_delete_entry_update(db, setup_entry_update):
    service = EntryUpdateService(db)
    entry_update = setup_entry_update

    assert service.delete_entry_update(entry_update.id) is True
    assert service.get_entry_update(entry_update.id) is None


def test_search_entry_updates(db, setup_entry_update):
    service = EntryUpdateService(db)
    entry_update = setup_entry_update

    # exact match by body
    results = service.search({"body": entry_update.body})
    assert len(results) == 1
    assert results[0].id == entry_update.id

    # ilike partial on body
    partial = entry_update.body[: max(1, len(entry_update.body) // 2)]
    results = service.search({"body": {"operator": "ilike", "value": f"%{partial}%"}})
    assert len(results) >= 1

    # filter by author_id
    results = service.search({"source_author_id": entry_update.source_author_id})
    assert len(results) >= 1

    # filter by entry_id
    results = service.search({"entry_id": entry_update.entry_id})
    assert len(results) >= 1

    # no match case
    results = service.search({"source_author_id": str(uuid4())})
    assert len(results) == 0
