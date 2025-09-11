from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment
from app.models.source_author import SourceAuthor
from app.schemas.comment import CommentCreate, CommentUpdate, Comment as CommentSchema
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class CommentService(SoftDeleteService[Comment]):
    def __init__(self, db: Session):
        super().__init__(db, Comment)

    def get_comment(self, comment_id: UUID) -> Optional[Comment]:
        return (
            self.db.query(Comment)
            .options(
                joinedload(Comment.source_author).selectinload(SourceAuthor.author),
            )
            .filter(Comment.id == comment_id)
            .first()
        )

    def get_comments(self, skip: int = 0, limit: int = 100) -> List[Comment]:
        return (
            self.db.query(Comment)
            .options(
                joinedload(Comment.source_author).selectinload(SourceAuthor.author),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_comment(self, comment: CommentCreate) -> Comment:
        db_comment = Comment(**comment.model_dump())
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        # Reload with source_author and author relationships
        return (
            self.db.query(Comment)
            .options(
                joinedload(Comment.source_author).selectinload(SourceAuthor.author),
            )
            .filter(Comment.id == db_comment.id)
            .first()
        )

    def update_comment(
        self, comment_id: UUID, comment: CommentUpdate
    ) -> Optional[Comment]:
        db_comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if db_comment:
            update_data = comment.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_comment, key, value)
            self.db.commit()
            self.db.refresh(db_comment)
            # Reload with source_author and author relationships
            return (
                self.db.query(Comment)
                .options(
                    joinedload(Comment.source_author).selectinload(SourceAuthor.author),
                )
                .filter(Comment.id == comment_id)
                .first()
            )
        return db_comment

    def delete_comment(self, comment_id: UUID) -> bool:
        return self.delete_record(comment_id)

    def get_comment_by_external_id(
        self, source_id: UUID, external_id: str
    ) -> Optional[Comment]:
        """Get a comment by source ID and external ID."""
        return (
            self.db.query(Comment)
            .options(
                joinedload(Comment.source_author).selectinload(SourceAuthor.author),
            )
            .filter(
                Comment.source_id == source_id,
                Comment.external_id == external_id,
            )
            .first()
        )

    def search(self, filters: Dict[str, Any]) -> List[CommentSchema]:
        query = self.db.query(Comment).options(
            joinedload(Comment.source_author).selectinload(SourceAuthor.author),
        )
        query = apply_filters(query, Comment, filters)
        return [CommentSchema.model_validate(comment) for comment in query.all()]
