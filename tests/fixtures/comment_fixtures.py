import pytest
from app.models.comment import Comment


@pytest.fixture
def setup_comment(db, setup_source_author, setup_entry, faker):
    """Create a test comment in the database with optional overrides."""
    source_author = setup_source_author
    entry = setup_entry

    comment_data = {
        "body": faker.text(200),
        "source_author_id": source_author.id,
        "entry_id": entry.id,
        "tags": ["feedback"],
        "labels": {"priority": "medium"},
        "meta_data": {"source": "test"},
    }

    comment = Comment(**comment_data)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
