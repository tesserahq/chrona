from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from app.models.entry_update import EntryUpdate
from app.models.source_author import SourceAuthor
from app.schemas.entry_update import EntryUpdateCreate, EntryUpdateUpdate, EntryUpdate as EntryUpdateSchema
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class EntryUpdateService(SoftDeleteService[EntryUpdate]):
    def __init__(self, db: Session):
        super().__init__(db, EntryUpdate)

    def get_entry_update(self, entry_update_id: UUID) -> Optional[EntryUpdate]:
        return (
            self.db.query(EntryUpdate)
            .options(
                joinedload(EntryUpdate.source_author).selectinload(SourceAuthor.author),
            )
            .filter(EntryUpdate.id == entry_update_id)
            .first()
        )

    def get_entry_updates(self, skip: int = 0, limit: int = 100) -> List[EntryUpdate]:
        return (
            self.db.query(EntryUpdate)
            .options(
                joinedload(EntryUpdate.source_author).selectinload(SourceAuthor.author),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_entry_update(self, entry_update: EntryUpdateCreate) -> EntryUpdate:
        db_entry_update = EntryUpdate(**entry_update.model_dump())
        self.db.add(db_entry_update)
        self.db.commit()
        self.db.refresh(db_entry_update)
        # Reload with source_author and author relationships
        return (
            self.db.query(EntryUpdate)
            .options(
                joinedload(EntryUpdate.source_author).selectinload(SourceAuthor.author),
            )
            .filter(EntryUpdate.id == db_entry_update.id)
            .first()
        )

    def update_entry_update(
        self, entry_update_id: UUID, entry_update: EntryUpdateUpdate
    ) -> Optional[EntryUpdate]:
        db_entry_update = self.db.query(EntryUpdate).filter(EntryUpdate.id == entry_update_id).first()
        if db_entry_update:
            update_data = entry_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_entry_update, key, value)
            self.db.commit()
            self.db.refresh(db_entry_update)
            # Reload with source_author and author relationships
            return (
                self.db.query(EntryUpdate)
                .options(
                    joinedload(EntryUpdate.source_author).selectinload(SourceAuthor.author),
                )
                .filter(EntryUpdate.id == entry_update_id)
                .first()
            )
        return db_entry_update

    def delete_entry_update(self, entry_update_id: UUID) -> bool:
        return self.delete_record(entry_update_id)

    def get_entry_update_by_external_id(
        self, source_id: UUID, external_id: str
    ) -> Optional[EntryUpdate]:
        """Get an entry update by source ID and external ID."""
        return (
            self.db.query(EntryUpdate)
            .options(
                joinedload(EntryUpdate.source_author).selectinload(SourceAuthor.author),
            )
            .filter(
                EntryUpdate.source_id == source_id,
                EntryUpdate.external_id == external_id,
            )
            .first()
        )

    def search(self, filters: Dict[str, Any]) -> List[EntryUpdateSchema]:
        query = self.db.query(EntryUpdate).options(
            joinedload(EntryUpdate.source_author).selectinload(SourceAuthor.author),
        )
        query = apply_filters(query, EntryUpdate, filters)
        return [EntryUpdateSchema.model_validate(entry_update) for entry_update in query.all()]
