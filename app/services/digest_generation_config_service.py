from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.digest_generation_config import DigestGenerationConfig
from app.schemas.digest_generation_config import (
    DigestGenerationConfigCreate,
    DigestGenerationConfigUpdate,
)
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters
from app.exceptions.resource_not_found_error import ResourceNotFoundError
from app.services.project_service import ProjectService


class DigestGenerationConfigService(SoftDeleteService[DigestGenerationConfig]):
    """Service class for managing DigestGenerationConfig entities."""

    def __init__(self, db: Session):
        super().__init__(db, DigestGenerationConfig)
        self.project_service = ProjectService(db)

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
        # Validate project exists
        project = self.project_service.get_project(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")

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
