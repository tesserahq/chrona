from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.author import Author
from app.schemas.author import AuthorCreate, AuthorUpdate, Author as AuthorSchema
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class AuthorService(SoftDeleteService[Author]):
    """Service class for managing Author entities."""

    def __init__(self, db: Session):
        super().__init__(db, Author)

    def get_author(self, author_id: UUID) -> Optional[Author]:
        """Get a single author by ID."""
        return self.db.query(Author).filter(Author.id == author_id).first()

    def get_authors(self, skip: int = 0, limit: int = 100) -> List[Author]:
        """Get a list of authors with pagination."""
        return self.db.query(Author).offset(skip).limit(limit).all()

    def get_authors_by_workspace(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Author]:
        """Get authors belonging to a specific workspace."""
        return (
            self.db.query(Author)
            .filter(Author.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_author(self, author: AuthorCreate, workspace_id: UUID) -> Author:
        """Create a new author."""
        author_data = author.model_dump()
        author_data["workspace_id"] = workspace_id
        db_author = Author(**author_data)
        self.db.add(db_author)
        self.db.commit()
        self.db.refresh(db_author)
        return db_author

    def update_author(self, author_id: UUID, author: AuthorUpdate) -> Optional[Author]:
        """Update an existing author."""
        db_author = self.db.query(Author).filter(Author.id == author_id).first()
        if db_author:
            update_data = author.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_author, key, value)
            self.db.commit()
            self.db.refresh(db_author)
        return db_author

    def delete_author(self, author_id: UUID) -> bool:
        """Delete an author (soft delete)."""
        return self.delete_record(author_id)

    def search(self, filters: Dict[str, Any]) -> List[AuthorSchema]:
        """Search authors based on provided filters."""
        query = self.db.query(Author)
        query = apply_filters(query, Author, filters)
        return [AuthorSchema.model_validate(author) for author in query.all()]
