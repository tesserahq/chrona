from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate, Source as SourceSchema
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class SourceService(SoftDeleteService[Source]):
    """Service class for managing Source entities."""

    def __init__(self, db: Session):
        super().__init__(db, Source)

    def get_source(self, source_id: UUID) -> Optional[Source]:
        """Get a single source by ID."""
        return self.db.query(Source).filter(Source.id == source_id).first()

    def get_sources(self, skip: int = 0, limit: int = 100) -> List[Source]:
        """Get a list of sources with pagination."""
        return self.db.query(Source).offset(skip).limit(limit).all()

    def get_sources_by_workspace(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Source]:
        """Get sources belonging to a specific workspace."""
        return (
            self.db.query(Source)
            .filter(Source.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_source(self, source: SourceCreate, workspace_id: UUID) -> Source:
        """Create a new source."""
        source_data = source.model_dump()
        source_data["workspace_id"] = workspace_id
        db_source = Source(**source_data)
        self.db.add(db_source)
        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def update_source(self, source_id: UUID, source: SourceUpdate) -> Optional[Source]:
        """Update an existing source."""
        db_source = self.db.query(Source).filter(Source.id == source_id).first()
        if db_source:
            update_data = source.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_source, key, value)
            self.db.commit()
            self.db.refresh(db_source)
        return db_source

    def delete_source(self, source_id: UUID) -> bool:
        """Delete a source (soft delete)."""
        return self.delete_record(source_id)

    def search(self, filters: Dict[str, Any]) -> List[SourceSchema]:
        """Search sources based on provided filters."""
        query = self.db.query(Source)
        query = apply_filters(query, Source, filters)
        return [SourceSchema.model_validate(source) for source in query.all()]

    def get_or_create_source_by_identifier(
        self,
        identifier: str,
        workspace_id: UUID,
        name: str = None,
        description: str = None,
    ) -> Source:
        """Get existing source by identifier or create a new one."""
        existing_source = (
            self.db.query(Source)
            .filter(
                Source.identifier == identifier, Source.workspace_id == workspace_id
            )
            .first()
        )

        if existing_source:
            return existing_source

        # Create new source
        source_data = SourceCreate(
            name=name or identifier,
            description=description or f"Source for {identifier}",
            identifier=identifier,
        )
        return self.create_source(source_data, workspace_id)
