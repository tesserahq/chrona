from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from app.models.digest import Digest
from app.models.entry import Entry
from app.schemas.digest import DigestCreate, DigestUpdate, ProjectDigestCreateRequest
from app.services.soft_delete_service import SoftDeleteService
from app.services.project_service import ProjectService
from app.exceptions.resource_not_found_error import ResourceNotFoundError
from app.utils.db.filtering import apply_filters


class DigestService(SoftDeleteService[Digest]):
    """Service class for managing Digest entities."""

    def __init__(self, db: Session):
        super().__init__(db, Digest)
        self.project_service = ProjectService(db)

    def get_digest(self, digest_id: UUID) -> Optional[Digest]:
        """Get a single digest by ID."""
        return (
            self.db.query(Digest)
            .options(selectinload(Digest.digest_generation_config))
            .filter(Digest.id == digest_id)
            .first()
        )

    def get_digest_with_entries(self, digest_id: UUID) -> Optional[Digest]:
        """Get a single digest by ID with its associated entries and entry_updates."""
        digest = (
            self.db.query(Digest)
            .options(selectinload(Digest.digest_generation_config))
            .filter(Digest.id == digest_id)
            .first()
        )
        if not digest:
            return None

        # Fetch entries based on the entry IDs stored in the digest
        if digest.entries_ids:
            entries = (
                self.db.query(Entry)
                .filter(Entry.id.in_(digest.entries_ids))
                .options(selectinload(Entry.entry_updates))
                .all()
            )
            # Manually attach entries to the digest object for serialization
            digest.entries = entries
        else:
            digest.entries = []

        return digest

    def get_digests(self, skip: int = 0, limit: int = 100) -> List[Digest]:
        """Get a list of digests with pagination."""
        return self.db.query(Digest).offset(skip).limit(limit).all()

    def get_digests_by_config(
        self, digest_generation_config_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Digest]:
        """Get digests belonging to a specific digest generation config."""
        return (
            self.db.query(Digest)
            .filter(Digest.digest_generation_config_id == digest_generation_config_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_digests_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Digest]:
        """Get digests belonging to a specific project."""
        return (
            self.db.query(Digest)
            .filter(Digest.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_digests_by_project_query(
        self, project_id: UUID, status: Optional[str] = None
    ):
        """Get query for digests belonging to a specific project for pagination."""
        query = (
            self.db.query(Digest)
            .options(selectinload(Digest.digest_generation_config))
            .filter(Digest.project_id == project_id)
            .order_by(Digest.created_at.desc())
        )

        if status:
            query = query.filter(Digest.status == status)
        return query

    def create_digest(
        self, digest: DigestCreate, created_at: Optional[datetime] = None
    ) -> Digest:
        """Create a new digest."""
        # Validate project exists
        if digest.project_id:
            project = self.project_service.get_project(digest.project_id)
            if not project:
                raise ResourceNotFoundError(
                    f"Project with ID {digest.project_id} not found"
                )

        digest_data = digest.model_dump()

        # Add created_at to the data if provided (for backfilling)
        if created_at is not None:
            digest_data["created_at"] = created_at

        db_digest = Digest(**digest_data)

        self.db.add(db_digest)
        self.db.commit()
        self.db.refresh(db_digest)
        return db_digest

    def create_project_digest(
        self, project_id: UUID, digest: ProjectDigestCreateRequest
    ) -> Digest:
        """Create a new digest scoped to a specific project."""

        from app.services.digest_generation_config_service import (  # Local import to avoid circular dependency
            DigestGenerationConfigService,
        )

        config_service = DigestGenerationConfigService(self.db)
        config = config_service.get_digest_generation_config(
            digest.digest_generation_config_id
        )
        if not config:
            raise ResourceNotFoundError(
                "Digest generation config "
                f"with ID {digest.digest_generation_config_id} not found"
            )

        if config.project_id != project_id:
            raise ResourceNotFoundError(
                "Digest generation config does not belong to the specified project"
            )

        digest_create = DigestCreate(
            **digest.model_dump(exclude_none=True),
            project_id=project_id,
        )

        return self.create_digest(digest_create)

    def update_digest(self, digest_id: UUID, digest: DigestUpdate) -> Optional[Digest]:
        """Update an existing digest."""
        db_digest = self.db.query(Digest).filter(Digest.id == digest_id).first()
        if db_digest:
            update_data = digest.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_digest, key, value)
            self.db.commit()
            self.db.refresh(db_digest)
        return db_digest

    def delete_digest(self, digest_id: UUID) -> bool:
        """Soft delete a digest."""
        return self.delete_record(digest_id)

    def get_digests_with_filters(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Digest]:
        """Get digests with optional filters applied."""
        query = self.db.query(Digest)
        if filters:
            query = apply_filters(query, Digest, filters)
        return query.offset(skip).limit(limit).all()

    def search_digests(
        self,
        project_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        labels: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Digest]:
        """
        Search digests by project_id, tags, labels, and other criteria.

        Args:
            project_id: Filter by project ID
            tags: Filter by tags (digests that have ANY of these tags)
            labels: Filter by labels (digests that have ALL of these label key-value pairs)
            status: Filter by digest status
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List[Digest]: List of digests matching the search criteria
        """
        query = self.db.query(Digest).options(
            selectinload(Digest.digest_generation_config)
        )

        # Filter by project_id if provided
        if project_id:
            query = query.filter(Digest.project_id == project_id)

        # Filter by status if provided
        if status:
            query = query.filter(Digest.status == status)

        # Apply tag filtering if tags are provided
        if tags:
            # Use PostgreSQL array overlap operator for efficient tag matching
            # This finds digests that have ANY of the specified tags
            query = query.filter(Digest.tags.overlap(tags))

        # Apply label filtering if labels are provided
        if labels:
            # Use PostgreSQL JSONB contains operator for efficient label matching
            # This finds digests that have ALL of the specified label key-value pairs
            for key, value in labels.items():
                query = query.filter(Digest.labels[key].astext == str(value))

        query = query.order_by(Digest.created_at.desc())

        # Apply pagination and execute query
        return query.offset(skip).limit(limit).all()
