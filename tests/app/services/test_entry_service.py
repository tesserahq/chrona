from uuid import uuid4
from sqlalchemy.orm import Session

from app.schemas.entry import EntryCreate, EntryUpdate
from app.services.entry_service import EntryService


def _sample_entry_input(setup_user, setup_project, faker):
    return EntryCreate(
        title=faker.sentence(nb_words=6),
        body=faker.text(200),
        source="import",
        external_id=faker.uuid4(),
        tags=["notes"],
        labels={"priority": "high"},
        meta_data={"ingested_by": "test"},
        author_id=setup_user.id,
        project_id=setup_project.id,
    )


def test_create_entry(db: Session, setup_user, setup_project, faker):
    service = EntryService(db)

    entry_in = _sample_entry_input(setup_user, setup_project, faker)
    entry = service.create_entry(entry_in)

    assert entry.id is not None
    assert entry.title == entry_in.title
    assert entry.author_id == setup_user.id
    assert entry.project_id == setup_project.id
    assert "notes" in entry.tags
    assert entry.labels["priority"] == "high"
    assert entry.meta_data["ingested_by"] == "test"


def test_get_entry(db: Session, setup_user, setup_project, faker):
    service = EntryService(db)
    entry = service.create_entry(_sample_entry_input(setup_user, setup_project, faker))

    retrieved = service.get_entry(entry.id)
    assert retrieved is not None
    assert retrieved.id == entry.id


def test_get_entries(db: Session, setup_user, setup_project, faker):
    service = EntryService(db)
    service.create_entry(_sample_entry_input(setup_user, setup_project, faker))
    entries = service.get_entries()
    assert isinstance(entries, list)
    assert len(entries) >= 1


def test_update_entry(db: Session, setup_user, setup_project, faker):
    service = EntryService(db)
    entry = service.create_entry(_sample_entry_input(setup_user, setup_project, faker))

    update = EntryUpdate(title="Updated Title", body="Updated body")
    updated = service.update_entry(entry.id, update)

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.body == "Updated body"


def test_delete_entry(db: Session, setup_user, setup_project, faker):
    service = EntryService(db)
    entry = service.create_entry(_sample_entry_input(setup_user, setup_project, faker))

    assert service.delete_entry(entry.id) is True
    assert service.get_entry(entry.id) is None


def test_search_entries(db: Session, setup_user, setup_project, faker):
    service = EntryService(db)
    entry = service.create_entry(_sample_entry_input(setup_user, setup_project, faker))

    # exact match by title
    results = service.search({"title": entry.title})
    assert len(results) == 1
    assert results[0].id == entry.id

    # ilike partial on title
    partial = entry.title[: max(1, len(entry.title)//2)]
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


