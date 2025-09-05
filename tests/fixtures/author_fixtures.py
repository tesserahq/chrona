import pytest
from app.models.author import Author


@pytest.fixture
def setup_author(db, setup_workspace, faker):
    """Create a test author in the database with optional overrides."""
    workspace = setup_workspace

    author_data = {
        "display_name": faker.name(),
        "avatar_url": faker.url(),
        "email": faker.email(),
        "tags": ["test"],
        "labels": {"type": "user"},
        "meta_data": {"source": "test"},
        "workspace_id": workspace.id,
    }

    author = Author(**author_data)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author
