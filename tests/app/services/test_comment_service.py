from uuid import uuid4
from sqlalchemy.orm import Session

from app.schemas.comment import CommentUpdate
from app.services.comment_service import CommentService


def test_create_comment(db: Session, setup_comment):
    service = CommentService(db)
    comment = setup_comment

    assert comment.id is not None
    assert comment.body is not None
    assert comment.author_id is not None
    assert comment.entry_id is not None
    assert "feedback" in comment.tags
    assert comment.labels["priority"] == "medium"
    assert comment.meta_data["source"] == "test"


def test_get_comment(db: Session, setup_comment):
    service = CommentService(db)
    comment = setup_comment

    retrieved = service.get_comment(comment.id)
    assert retrieved is not None
    assert retrieved.id == comment.id


def test_get_comments(db: Session, setup_comment):
    service = CommentService(db)
    comment = setup_comment
    comments = service.get_comments()
    assert isinstance(comments, list)
    assert len(comments) >= 1


def test_update_comment(db: Session, setup_comment):
    service = CommentService(db)
    comment = setup_comment

    update = CommentUpdate(body="Updated comment body", tags=["updated"])
    updated = service.update_comment(comment.id, update)

    assert updated is not None
    assert updated.body == "Updated comment body"
    assert "updated" in updated.tags


def test_delete_comment(db: Session, setup_comment):
    service = CommentService(db)
    comment = setup_comment

    assert service.delete_comment(comment.id) is True
    assert service.get_comment(comment.id) is None


def test_search_comments(db: Session, setup_comment):
    service = CommentService(db)
    comment = setup_comment

    # exact match by body
    results = service.search({"body": comment.body})
    assert len(results) == 1
    assert results[0].id == comment.id

    # ilike partial on body
    partial = comment.body[: max(1, len(comment.body) // 2)]
    results = service.search({"body": {"operator": "ilike", "value": f"%{partial}%"}})
    assert len(results) >= 1

    # filter by author_id
    results = service.search({"author_id": comment.author_id})
    assert len(results) >= 1

    # filter by entry_id
    results = service.search({"entry_id": comment.entry_id})
    assert len(results) >= 1

    # no match case
    results = service.search({"author_id": str(uuid4())})
    assert len(results) == 0
