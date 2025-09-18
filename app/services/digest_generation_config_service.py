from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
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
from app.utils.date_filter import calculate_digest_date_range


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

    def get_entries_for_digest(
        self,
        digest_generation_config_id: UUID,
        execution_time: Optional[datetime] = None,
    ) -> Tuple[List[Entry], List[EntryUpdate], DigestGenerationConfig]:
        """Get all entries and entry updates for a digest generation config.

        Returns entries that:
        - Belong to the specified project
        - Match the filter_tags and filter_labels (if specified)
        - Have entry updates created within the calculated date range based on cron expression

        Args:
            digest_generation_config_id: ID of the digest generation config
            execution_time: Time when the digest is being generated (defaults to now)

        Returns:
            tuple: (entries, entry_updates, config)
        """
        # Get the digest generation config
        config = self.get_digest_generation_config(digest_generation_config_id)
        if not config:
            raise ResourceNotFoundError(
                f"Digest generation config with ID {digest_generation_config_id} not found"
            )

        # Calculate date range based on cron expression and timezone
        start_date, end_date = calculate_digest_date_range(
            str(config.cron_expression), str(config.timezone), execution_time
        )

        # Build the query to find entries with entry updates in the calculated date range
        # Join entries with entry_updates and filter by entry_update.source_created_at
        query = (
            self.db.query(Entry)
            .join(EntryUpdate, Entry.id == EntryUpdate.entry_id)
            .filter(
                and_(
                    Entry.project_id == config.project_id,
                    EntryUpdate.source_created_at >= start_date,
                    EntryUpdate.source_created_at <= end_date,
                    EntryUpdate.deleted_at.is_(None),
                    Entry.deleted_at.is_(None),
                )
            )
        )

        # Apply filter_tags if specified
        if config.filter_tags:
            query = query.filter(Entry.tags.overlap(config.filter_tags))

        # Apply filter_labels if specified
        if config.filter_labels:
            for key, value in config.filter_labels.items():
                query = query.filter(Entry.labels[key].astext == str(value))

        # Get matching entries (distinct to avoid duplicates from multiple entry updates)
        entries = query.distinct().all()

        if not entries and not config.generate_empty_digest:
            raise ResourceNotFoundError("No entries found matching the criteria")

        # Get all entry updates for these entries that were created in the calculated date range
        entry_ids = [entry.id for entry in entries]
        entry_updates = (
            self.db.query(EntryUpdate)
            .filter(
                and_(
                    EntryUpdate.entry_id.in_(entry_ids),
                    EntryUpdate.source_created_at >= start_date,
                    EntryUpdate.source_created_at <= end_date,
                    EntryUpdate.deleted_at.is_(None),
                )
            )
            .order_by(desc(EntryUpdate.source_created_at))
            .all()
        )

        return entries, entry_updates, config

    def format_digest_body(
        self, entries: List[Entry], entry_updates: List[EntryUpdate]
    ) -> str:
        """Format the digest body content from entries and entry updates.

        Args:
            entries: List of entries to include in the digest
            entry_updates: List of entry updates to include in the digest

        Returns:
            Formatted digest body as a string
        """
        digest_body_parts = []

        for entry in entries:
            # Find the latest update for this entry
            latest_update = next(
                (update for update in entry_updates if update.entry_id == entry.id),
                None,
            )

            digest_body_parts.append(f"* {entry.title}")
            if entry.body:
                digest_body_parts.append(str(entry.body))
            if latest_update and latest_update.body:
                digest_body_parts.append(f"Latest update: {latest_update.body}")
            digest_body_parts.append("")  # Empty line between entries

        return "\n".join(digest_body_parts)

    def create_digest_from_entries(
        self,
        entries: List[Entry],
        entry_updates: List[EntryUpdate],
        config: DigestGenerationConfig,
        execution_time: Optional[datetime] = None,
    ) -> Digest:
        """Create a digest from entries and entry updates.

        Args:
            entries: List of entries to include in the digest
            entry_updates: List of entry updates to include in the digest
            config: The digest generation config
            execution_time: Time when the digest is being generated (defaults to now)

        Returns:
            The created digest
        """
        # Get entry IDs and entry update IDs
        entry_ids: List[UUID] = [UUID(str(entry.id)) for entry in entries]
        entry_updates_ids: List[UUID] = [
            UUID(str(update.id)) for update in entry_updates
        ]

        # Generate the digest body using the formatting function
        digest_body = self.format_digest_body(entries, entry_updates)

        # Calculate the date range based on cron expression and timezone
        from_date, to_date = calculate_digest_date_range(
            str(config.cron_expression), str(config.timezone), execution_time
        )

        # Create the draft digest
        digest_data = DigestCreate(
            title=f"Draft Digest - {config.title}",
            body=digest_body,
            raw_body=digest_body,  # Set raw_body to the same as body for now
            entries_ids=entry_ids,
            entry_updates_ids=entry_updates_ids,
            from_date=from_date,
            to_date=to_date,
            digest_generation_config_id=UUID(str(config.id)),
            project_id=UUID(str(config.project_id)),
            tags=list(config.tags) if config.tags else [],
            labels=dict(config.labels) if config.labels else {},
            status=DigestStatuses.DRAFT,
        )

        # Create the digest with draft status
        digest = self.digest_service.create_digest(digest_data)

        return digest

    def generate_draft_digest(
        self,
        digest_generation_config_id: UUID,
        execution_time: Optional[datetime] = None,
    ) -> Digest:
        """Generate a draft digest for a digest generation config."""
        # Get entries and entry updates for the digest
        entries, entry_updates, config = self.get_entries_for_digest(
            digest_generation_config_id, execution_time
        )

        # Create the digest from the entries
        digest = self.create_digest_from_entries(
            entries, entry_updates, config, execution_time
        )

        return digest
