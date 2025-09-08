from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.source_author import SourceAuthor
from app.schemas.source_author import (
    SourceAuthorCreate,
    SourceAuthorUpdate,
    SourceAuthor as SourceAuthorSchema,
)
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class SourceAuthorService(SoftDeleteService[SourceAuthor]):
    """Service class for managing SourceAuthor entities."""

    def __init__(self, db: Session):
        super().__init__(db, SourceAuthor)

    def get_source_author(self, source_author_id: UUID) -> Optional[SourceAuthor]:
        """Get a single source author by ID."""
        return (
            self.db.query(SourceAuthor)
            .filter(SourceAuthor.id == source_author_id)
            .first()
        )

    def get_source_authors(self, skip: int = 0, limit: int = 100) -> List[SourceAuthor]:
        """Get a list of source authors with pagination."""
        return self.db.query(SourceAuthor).offset(skip).limit(limit).all()

    def get_source_authors_by_source(
        self, source_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[SourceAuthor]:
        """Get source authors belonging to a specific source."""
        return (
            self.db.query(SourceAuthor)
            .filter(SourceAuthor.source_id == source_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_source_author_by_external_id(
        self, source_id: UUID, source_author_id: str
    ) -> Optional[SourceAuthor]:
        """Get a source author by source ID and external author ID."""
        return (
            self.db.query(SourceAuthor)
            .filter(
                SourceAuthor.source_id == source_id,
                SourceAuthor.source_author_id == source_author_id,
            )
            .first()
        )

    def create_source_author(self, source_author: SourceAuthorCreate) -> SourceAuthor:
        """Create a new source author."""
        db_source_author = SourceAuthor(**source_author.model_dump())
        self.db.add(db_source_author)
        self.db.commit()
        self.db.refresh(db_source_author)
        return db_source_author

    def get_or_create_source_author(
        self, source_id: UUID, author_id: UUID, source_author_id: str
    ) -> SourceAuthor:
        """Get existing source author or create a new one."""
        existing = self.get_source_author_by_external_id(source_id, source_author_id)
        if existing:
            return existing

        source_author_data = SourceAuthorCreate(
            author_id=author_id, source_id=source_id, source_author_id=source_author_id
        )
        return self.create_source_author(source_author_data)

    def update_source_author(
        self, source_author_id: UUID, source_author: SourceAuthorUpdate
    ) -> Optional[SourceAuthor]:
        """Update an existing source author."""
        db_source_author = (
            self.db.query(SourceAuthor)
            .filter(SourceAuthor.id == source_author_id)
            .first()
        )
        if db_source_author:
            update_data = source_author.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_source_author, key, value)
            self.db.commit()
            self.db.refresh(db_source_author)
        return db_source_author

    def delete_source_author(self, source_author_id: UUID) -> bool:
        """Delete a source author (soft delete)."""
        return self.delete_record(source_author_id)

    def search(self, filters: Dict[str, Any]) -> List[SourceAuthorSchema]:
        """Search source authors based on provided filters."""
        query = self.db.query(SourceAuthor)
        query = apply_filters(query, SourceAuthor, filters)
        return [
            SourceAuthorSchema.model_validate(source_author)
            for source_author in query.all()
        ]
