import pytest
from app.models.source import Source


@pytest.fixture
def setup_source(db, setup_workspace, faker):
    """Create a test source in the database with optional overrides."""
    workspace = setup_workspace

    source_data = {
        "name": faker.word(),
        "description": faker.text(100),
        "identifier": str(faker.uuid4()),
        "workspace_id": workspace.id,
    }

    source = Source(**source_data)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
