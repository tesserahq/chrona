import pytest
from app.models.import_request import ImportRequest
from app.models.import_request_item import ImportRequestItem


@pytest.fixture
def setup_import_request(db, setup_user, setup_project, setup_source, faker):
    """Create an import request for testing purposes."""
    user = setup_user
    project = setup_project
    source = setup_source

    import_request = ImportRequest(
        source_id=source.id,
        requested_by_id=user.id,
        status="pending",
        received_count=faker.random_int(min=0, max=100),
        success_count=0,
        failure_count=0,
        options={"format": "csv", "delimiter": ","},
        project_id=project.id,
    )
    db.add(import_request)
    db.commit()
    db.refresh(import_request)
    return import_request


@pytest.fixture
def setup_another_import_request(
    db, setup_another_user, setup_project, setup_source, faker
):
    """Create another import request for testing purposes."""
    user = setup_another_user
    project = setup_project
    source = setup_source

    import_request = ImportRequest(
        source_id=setup_source.id,
        requested_by_id=user.id,
        status="completed",
        received_count=faker.random_int(min=1, max=50),
        success_count=faker.random_int(min=1, max=50),
        failure_count=0,
        options={"format": "json"},
        project_id=project.id,
    )
    db.add(import_request)
    db.commit()
    db.refresh(import_request)
    return import_request


@pytest.fixture
def setup_import_request_item(db, setup_import_request, setup_source, faker):
    """Create an import request item for testing purposes."""
    source = setup_source
    import_request = setup_import_request

    import_request_item = ImportRequestItem(
        import_request_id=import_request.id,
        source_id=source.id,
        source_item_id=str(faker.uuid4()),
        raw_payload={"title": faker.sentence(), "content": faker.text()},
        status="pending",
    )
    db.add(import_request_item)
    db.commit()
    db.refresh(import_request_item)
    return import_request_item


@pytest.fixture
def setup_another_import_request_item(db, setup_import_request, setup_source, faker):
    """Create another import request item for testing purposes."""
    source = setup_source
    import_request = setup_import_request

    import_request_item = ImportRequestItem(
        import_request_id=import_request.id,
        source_id=source.id,
        source_item_id=str(faker.uuid4()),
        raw_payload={"title": faker.sentence(), "content": faker.text()},
        status="completed",
    )
    db.add(import_request_item)
    db.commit()
    db.refresh(import_request_item)
    return import_request_item


@pytest.fixture
def setup_import_request_with_items(db, setup_import_request, setup_source, faker):
    """Create an import request with multiple items for testing purposes."""
    source = setup_source
    import_request = setup_import_request

    items = []
    for i in range(3):
        item = ImportRequestItem(
            import_request_id=import_request.id,
            source_id=source.id,
            source_item_id=str(faker.uuid4()),
            raw_payload={"title": faker.sentence(), "content": faker.text()},
            status="pending" if i < 2 else "completed",
        )
        db.add(item)
        items.append(item)

    db.commit()
    for item in items:
        db.refresh(item)

    return setup_import_request, items
