from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.digest import Digest
from app.schemas.digest import DigestCreate, DigestUpdate, Digest as DigestSchema
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
        return self.db.query(Digest).filter(Digest.id == digest_id).first()

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

    def create_digest(self, digest: DigestCreate) -> Digest:
        """Create a new digest."""
        # Validate project exists
        if digest.project_id:
            project = self.project_service.get_project(digest.project_id)
            if not project:
                raise ResourceNotFoundError(
                    f"Project with ID {digest.project_id} not found"
                )

        digest_data = digest.model_dump()
        db_digest = Digest(**digest_data)
        self.db.add(db_digest)
        self.db.commit()
        self.db.refresh(db_digest)
        return db_digest

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
