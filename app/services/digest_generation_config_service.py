from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime, date
from app.models.digest_generation_config import DigestGenerationConfig
from app.models.entry import Entry
from app.models.entry_update import EntryUpdate
from app.models.digest import Digest
from app.schemas.digest_generation_config import (
    DigestGenerationConfigCreate,
    DigestGenerationConfigUpdate,
)
from app.schemas.digest import DigestCreate
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters
from app.exceptions.resource_not_found_error import ResourceNotFoundError
from app.services.digest_service import DigestService
from app.constants.digest_constants import DigestStatuses


class DigestGenerationConfigService(SoftDeleteService[DigestGenerationConfig]):
    """Service class for managing DigestGenerationConfig entities."""

    def __init__(self, db: Session):
        super().__init__(db, DigestGenerationConfig)
        self.digest_service = DigestService(db)

    def get_digest_generation_config(
        self, digest_generation_config_id: UUID
    ) -> Optional[DigestGenerationConfig]:
        """Get a single digest definition by ID."""
        return (
            self.db.query(DigestGenerationConfig)
            .filter(DigestGenerationConfig.id == digest_generation_config_id)
            .first()
        )

    def get_digest_generation_configs(
        self, skip: int = 0, limit: int = 100
    ) -> List[DigestGenerationConfig]:
        """Get a list of digest definitions with pagination."""
        return self.db.query(DigestGenerationConfig).offset(skip).limit(limit).all()

    def get_digest_generation_configs_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[DigestGenerationConfig]:
        """Get digest definitions belonging to a specific project."""
        return (
            self.db.query(DigestGenerationConfig)
            .filter(DigestGenerationConfig.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_digest_generation_configs_by_project_query(self, project_id: UUID):
        """Get a query object for digest generation configs by project for use with fastapi-pagination."""
        return self.db.query(DigestGenerationConfig).filter(
            DigestGenerationConfig.project_id == project_id
        )

    def create_digest_generation_config(
        self, digest_generation_config: DigestGenerationConfigCreate, project_id: UUID
    ) -> DigestGenerationConfig:
        """Create a new digest definition."""

        digest_generation_config_data = digest_generation_config.model_dump()
        digest_generation_config_data["project_id"] = project_id

        db_digest_generation_config = DigestGenerationConfig(
            **digest_generation_config_data
        )
        self.db.add(db_digest_generation_config)
        self.db.commit()
        self.db.refresh(db_digest_generation_config)
        return db_digest_generation_config

    def update_digest_generation_config(
        self,
        digest_generation_config_id: UUID,
        digest_generation_config: DigestGenerationConfigUpdate,
    ) -> Optional[DigestGenerationConfig]:
        """Update a digest definition."""
        db_digest_generation_config = (
            self.db.query(DigestGenerationConfig)
            .filter(DigestGenerationConfig.id == digest_generation_config_id)
            .first()
        )

        if db_digest_generation_config:
            update_data = digest_generation_config.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_digest_generation_config, key, value)
            self.db.commit()
            self.db.refresh(db_digest_generation_config)

        return db_digest_generation_config

    def delete_digest_generation_config(
        self, digest_generation_config_id: UUID
    ) -> bool:
        """Soft delete a digest definition."""
        return self.delete_record(digest_generation_config_id)

    def search_digest_generation_configs(
        self, filters: Dict[str, Any]
    ) -> List[DigestGenerationConfig]:
        """Search digest definitions with filters."""
        query = self.db.query(DigestGenerationConfig)
        filtered_query = apply_filters(query, DigestGenerationConfig, filters)
        return filtered_query.all()

    def search_digest_generation_configs_query(self, filters: Dict[str, Any]):
        """Get a query object for digest generation config search for use with fastapi-pagination."""
        query = self.db.query(DigestGenerationConfig)
        filtered_query = apply_filters(query, DigestGenerationConfig, filters)
        return filtered_query

    def generate_draft_digest(self, digest_generation_config_id: UUID) -> Digest:
        """Generate a draft digest for a digest generation config."""
        # Get the digest generation config
        config = self.get_digest_generation_config(digest_generation_config_id)
        if not config:
            raise ResourceNotFoundError(
                f"Digest generation config with ID {digest_generation_config_id} not found"
            )

        # Get today's date range for filtering entries (from beginning of day until now)
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        now = datetime.now()

        # Build the query for entries matching the criteria
        query = self.db.query(Entry).filter(
            and_(
                Entry.project_id == config.project_id,
                Entry.created_at >= start_of_day,
                Entry.created_at <= now,
                Entry.deleted_at.is_(None),
            )
        )

        # Apply filter_tags if specified
        if config.filter_tags:
            query = query.filter(Entry.tags.overlap(config.filter_tags))

        # Apply filter_labels if specified
        if config.filter_labels:
            for key, value in config.filter_labels.items():
                query = query.filter(Entry.labels[key].astext == str(value))

        # Get matching entries
        entries = query.all()

        if not entries and not config.generate_empty_digest:
            raise ResourceNotFoundError("No entries found matching the criteria")

        # Get entry IDs
        entry_ids = [entry.id for entry in entries]

        # Get the latest entry update for each entry
        entry_updates = []
        entry_updates_ids = []

        # TODO: This can be optimized.
        for entry in entries:
            latest_update = (
                self.db.query(EntryUpdate)
                .filter(
                    and_(
                        EntryUpdate.entry_id == entry.id,
                        EntryUpdate.deleted_at.is_(None),
                    )
                )
                .order_by(desc(EntryUpdate.created_at))
                .first()
            )

            if latest_update:
                entry_updates.append(latest_update)
                entry_updates_ids.append(latest_update.id)

        # Generate the digest body
        digest_body_parts = []
        for entry in entries:
            # Find the latest update for this entry
            latest_update = next(
                (update for update in entry_updates if update.entry_id == entry.id),
                None,
            )

            digest_body_parts.append(f"* {entry.title}")
            if entry.body:
                digest_body_parts.append(entry.body)
            if latest_update and latest_update.body:
                digest_body_parts.append(f"Latest update: {latest_update.body}")
            digest_body_parts.append("")  # Empty line between entries

        digest_body = "\n".join(digest_body_parts)

        # Create the draft digest
        digest_data = DigestCreate(
            title=f"Draft Digest - {config.title}",
            body=digest_body,
            entries_ids=entry_ids,
            entry_updates_ids=entry_updates_ids,
            from_date=datetime.combine(today, datetime.min.time()),
            to_date=datetime.combine(today, datetime.max.time()),
            digest_generation_config_id=config.id,
            project_id=config.project_id,
            tags=config.tags.copy(),
            labels=config.labels.copy(),
            status=DigestStatuses.DRAFT,
        )

        # Create the digest with draft status
        digest = self.digest_service.create_digest(digest_data)

        return digest
