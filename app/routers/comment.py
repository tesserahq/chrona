from app.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    Comment,
)
from app.services.comment_service import CommentService
from app.models.comment import Comment as CommentModel
from app.models.entry import Entry as EntryModel
from app.routers.utils.dependencies import get_comment_by_id, get_entry_by_id
from app.schemas.common import ListResponse

router = APIRouter(prefix="/entries/{entry_id}/comments", tags=["comments"])
standalone_router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("", response_model=ListResponse[Comment])
def list_comments(
    entry: EntryModel = Depends(get_entry_by_id),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all comments for a specific entry with pagination."""
    service = CommentService(db)
    # Filter comments by entry_id
    comments = service.search({"entry_id": entry.id})
    # Apply pagination manually since we're using search
    comments = comments[skip : skip + limit]
    return ListResponse(data=comments)


@router.post("", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment: CommentCreate,
    entry: EntryModel = Depends(get_entry_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new comment for a specific entry."""
    service = CommentService(db)
    # Ensure the comment belongs to the specified entry
    comment.entry_id = entry.id
    return service.create_comment(comment)


@standalone_router.get("/{comment_id}", response_model=Comment)
def get_comment(
    comment: CommentModel = Depends(get_comment_by_id),
    current_user=Depends(get_current_user),
):
    """Get a specific comment by ID."""
    return comment


@standalone_router.put("/{comment_id}", response_model=Comment)
def update_comment(
    comment_update: CommentUpdate,
    comment: CommentModel = Depends(get_comment_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing comment."""
    service = CommentService(db)
    updated = service.update_comment(comment.id, comment_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return updated


@standalone_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment: CommentModel = Depends(get_comment_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a comment."""
    service = CommentService(db)
    success = service.delete_comment(comment.id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"message": "Comment deleted successfully"}
