from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.author import Author
from app.models.source_author import SourceAuthor
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

    def get_authors_by_workspace_query(self, workspace_id: UUID):
        """Get a query object for authors by workspace for use with fastapi-pagination."""
        return (
            self.db.query(Author)
            .filter(Author.workspace_id == workspace_id)
            .order_by(Author.display_name.asc())
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

    def merge_authors(self, author_ids: List[UUID], merge_to_author_id: UUID) -> bool:
        """
        Merge multiple authors into a single author.

        This function:
        1. Validates that all authors exist and belong to the same workspace
        2. Updates all source_author records to point to the merge_to author
        3. Soft deletes the original authors

        Note: Assumes that the merge_to author and source combinations don't already exist,
        so no duplicate checking is performed. All source_author records are simply
        reassigned to maintain entry relationships.

        Args:
            author_ids: List of author IDs to merge from
            merge_to_author_id: ID of the author to merge into

        Returns:
            bool: True if merge was successful, False otherwise

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraints are violated
        """
        if not author_ids:
            raise ValueError("At least one author ID must be provided to merge")

        if merge_to_author_id in author_ids:
            raise ValueError(
                "merge_to_author_id cannot be in the list of authors to merge"
            )

        try:
            # Validate that the merge_to author exists
            merge_to_author = self.get_author(merge_to_author_id)
            if not merge_to_author:
                raise ValueError(
                    f"Target author with ID {merge_to_author_id} not found"
                )

            # Validate that all authors to merge exist and belong to same workspace
            authors_to_merge = []
            for author_id in author_ids:
                author = self.get_author(author_id)
                if not author:
                    raise ValueError(f"Author with ID {author_id} not found")
                if author.workspace_id != merge_to_author.workspace_id:
                    raise ValueError(
                        f"Author {author_id} belongs to different workspace than target author"
                    )
                authors_to_merge.append(author)

            # Begin transaction - update all source_author records
            source_authors_updated = 0
            for author_id in author_ids:
                # Update all source_author records to point to the merge_to author
                source_authors = (
                    self.db.query(SourceAuthor)
                    .filter(SourceAuthor.author_id == author_id)
                    .all()
                )

                for source_author in source_authors:
                    # Update to point to merge_to author
                    setattr(source_author, "author_id", merge_to_author_id)
                    source_authors_updated += 1

            # Soft delete the original authors
            for author_id in author_ids:
                self.delete_record(author_id)

            # Commit all changes
            self.db.commit()

            return True

        except (ValueError, IntegrityError) as e:
            # Rollback on any error
            self.db.rollback()
            raise e
        except Exception as e:
            # Rollback on unexpected errors
            self.db.rollback()
            raise RuntimeError(f"Unexpected error during author merge: {str(e)}")
