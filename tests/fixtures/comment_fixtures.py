import pytest
from app.models.comment import Comment
from sqlalchemy.orm import Session


@pytest.fixture
def setup_comment(db: Session, setup_user, setup_entry, faker):
    """Create a test comment in the database with optional overrides."""
    user = setup_user
    entry = setup_entry

    comment_data = {
        "body": faker.text(200),
        "author_id": user.id,
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
