from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.entry import Entry
from app.models.source_author import SourceAuthor
from app.schemas.entry import EntryCreate, EntryUpdate
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class EntryService(SoftDeleteService[Entry]):
    def __init__(self, db: Session):
        super().__init__(db, Entry)

    def get_entry(self, entry_id: UUID) -> Optional[Entry]:
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.comments),
            )
            .filter(Entry.id == entry_id)
            .first()
        )

    def get_entries(self, skip: int = 0, limit: int = 100) -> List[Entry]:
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.comments),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_entries_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Entry]:
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.comments),
            )
            .filter(Entry.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_entries_by_project_query(self, project_id: UUID):
        """Get a query object for entries by project for use with fastapi-pagination."""
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.comments),
            )
            .filter(Entry.project_id == project_id)
        )

    def create_entry(self, entry: EntryCreate) -> Entry:
        db_entry = Entry(**entry.model_dump())
        self.db.add(db_entry)
        self.db.commit()
        self.db.refresh(db_entry)
        # Reload with source, source_author, and comments relationships
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.comments),
            )
            .filter(Entry.id == db_entry.id)
            .first()
        )

    def update_entry(self, entry_id: UUID, entry: EntryUpdate) -> Optional[Entry]:
        db_entry = self.db.query(Entry).filter(Entry.id == entry_id).first()
        if db_entry:
            update_data = entry.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_entry, key, value)
            self.db.commit()
            self.db.refresh(db_entry)
            # Reload with source, source_author, and comments relationships
            return (
                self.db.query(Entry)
                .options(
                    joinedload(Entry.source),
                    joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                    selectinload(Entry.comments),
                )
                .filter(Entry.id == entry_id)
                .first()
            )
        return db_entry

    def delete_entry(self, entry_id: UUID) -> bool:
        return self.delete_record(entry_id)

    def get_entry_by_external_id(
        self, source_id: UUID, external_id: str
    ) -> Optional[Entry]:
        """Get an entry by source ID and external ID."""
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.comments),
            )
            .filter(
                Entry.source_id == source_id,
                Entry.external_id == external_id,
            )
            .first()
        )

    def search(self, filters: Dict[str, Any]) -> List[Entry]:
        query = self.db.query(Entry).options(
            joinedload(Entry.source),
            joinedload(Entry.source_author).joinedload(SourceAuthor.author),
            selectinload(Entry.comments),
        )
        query = apply_filters(query, Entry, filters)
        return query.all()

    def search_query(self, filters: Dict[str, Any]):
        """Get a query object for entry search for use with fastapi-pagination."""
        query = self.db.query(Entry).options(
            joinedload(Entry.source),
            joinedload(Entry.source_author).joinedload(SourceAuthor.author),
            selectinload(Entry.comments),
        )
        query = apply_filters(query, Entry, filters)
        return query
