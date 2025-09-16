from typing import List, Optional, Dict, Any
from uuid import UUID
import secrets
from app.exceptions.resource_not_found_error import ResourceNotFoundError
from sqlalchemy.orm import Session
from app.models.gazette import Gazette
from app.models.digest import Digest
from app.schemas.gazette import GazetteCreate, GazetteUpdate, Gazette as GazetteSchema
from app.schemas.digest import Digest as DigestSchema
from app.services.project_service import ProjectService
from app.utils.db.filtering import apply_filters
from app.services.soft_delete_service import SoftDeleteService
from app.constants.digest_constants import DigestStatuses


class GazetteService(SoftDeleteService[Gazette]):
    def __init__(self, db: Session):
        super().__init__(db, Gazette)
        self.project_service = ProjectService(db)

    def get_gazette(self, gazette_id: UUID) -> Optional[Gazette]:
        """Fetch a single gazette by ID."""
        return self.db.query(Gazette).filter(Gazette.id == gazette_id).first()

    def get_gazettes(self, skip: int = 0, limit: int = 100) -> List[Gazette]:
        """Fetch a list of gazettes with pagination."""
        return self.db.query(Gazette).offset(skip).limit(limit).all()

    def create_gazette(self, gazette: GazetteCreate) -> Gazette:
        """Create a new gazette."""
        # Validate project exists
        project = self.project_service.get_project(gazette.project_id)
        if not project:
            raise ResourceNotFoundError(
                f"Project with ID {gazette.project_id} not found"
            )

        data = gazette.model_dump()
        db_gazette = Gazette(**data)
        self.db.add(db_gazette)
        self.db.commit()
        self.db.refresh(db_gazette)

        return db_gazette

    def update_gazette(
        self, gazette_id: UUID, gazette: GazetteUpdate
    ) -> Optional[Gazette]:
        """Update an existing gazette."""
        db_gazette = self.db.query(Gazette).filter(Gazette.id == gazette_id).first()
        if db_gazette:
            update_data = gazette.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_gazette, key, value)
            self.db.commit()
            self.db.refresh(db_gazette)
        return db_gazette

    def delete_gazette(self, gazette_id: UUID) -> bool:
        """Soft delete a gazette."""
        db_gazette = self.db.query(Gazette).filter(Gazette.id == gazette_id).first()
        if db_gazette:
            return self.delete_record(gazette_id)
        return False

    def search(self, filters: Dict[str, Any]) -> List[GazetteSchema]:
        """
        Search gazettes based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%keyword%"}

        Returns:
            List[GazetteSchema]: List of gazettes matching the filter criteria.
        """
        query = self.db.query(Gazette)
        query = apply_filters(query, Gazette, filters)
        return [GazetteSchema.model_validate(gazette) for gazette in query.all()]

    def get_gazettes_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Gazette]:
        """Get all gazettes for a specific project."""
        return (
            self.db.query(Gazette)
            .filter(Gazette.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_gazettes_by_project_query(self, project_id: UUID):
        """Get a query for gazettes by project (for pagination)."""
        return self.db.query(Gazette).filter(Gazette.project_id == project_id)

    def get_gazette_by_share_key(self, share_key: str) -> Optional[Gazette]:
        """Get a gazette by its share key."""
        return self.db.query(Gazette).filter(Gazette.share_key == share_key).first()

    def generate_share_key(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure URL-safe share key.

        Args:
            length: The number of bytes to use for the token. Default is 16 bytes,
                   which produces a ~22 character URL-safe string.

        Returns:
            str: A URL-safe string suitable for use as a share key.
        """
        return secrets.token_urlsafe(length)

    def generate_unique_share_key(
        self, length: int = 16, max_attempts: int = 10
    ) -> str:
        """
        Generate a unique share key that doesn't already exist in the database.

        Args:
            length: The number of bytes to use for the token. Default is 16 bytes.
            max_attempts: Maximum number of attempts to generate a unique key.

        Returns:
            str: A unique URL-safe string suitable for use as a share key.

        Raises:
            RuntimeError: If unable to generate a unique key after max_attempts.
        """
        for _ in range(max_attempts):
            share_key = self.generate_share_key(length)
            # Check if this share key already exists
            existing = self.get_gazette_by_share_key(share_key)
            if not existing:
                return share_key

        raise RuntimeError(
            f"Unable to generate unique share key after {max_attempts} attempts"
        )

    def generate_or_get_share_key(self, gazette_id: UUID) -> Gazette:
        """
        Generate a share key for a gazette if it doesn't exist, or return existing one.
        Updates the gazette record and returns the updated gazette.

        Args:
            gazette_id: The UUID of the gazette to generate/get share key for

        Returns:
            Gazette: The updated gazette with share_key

        Raises:
            ResourceNotFoundError: If gazette is not found
            RuntimeError: If unable to generate unique share key
        """
        gazette = self.get_gazette(gazette_id)
        if not gazette:
            raise ResourceNotFoundError(f"Gazette with ID {gazette_id} not found")

        # If gazette already has a share key, return it
        if gazette.share_key:
            return gazette

        # Generate a unique share key
        share_key = self.generate_unique_share_key()

        # Update the gazette with the new share key
        gazette.share_key = share_key
        self.db.commit()
        self.db.refresh(gazette)

        return gazette

    def regenerate_share_key(self, gazette_id: UUID) -> Gazette:
        """
        Regenerate the share key for a gazette, replacing any existing one.
        Updates the gazette record and returns the updated gazette.

        Args:
            gazette_id: The UUID of the gazette to regenerate share key for

        Returns:
            Gazette: The updated gazette with new share_key

        Raises:
            ResourceNotFoundError: If gazette is not found
            RuntimeError: If unable to generate unique share key
        """
        gazette = self.get_gazette(gazette_id)
        if not gazette:
            raise ResourceNotFoundError(f"Gazette with ID {gazette_id} not found")

        # Generate a new unique share key (always generate new one)
        share_key = self.generate_unique_share_key()

        # Update the gazette with the new share key
        gazette.share_key = share_key
        self.db.commit()
        self.db.refresh(gazette)

        return gazette

    def get_gazette_digests(self, gazette: Gazette) -> List[DigestSchema]:
        """
        Get published digests from the gazette's project that match the gazette's tags/labels.

        Args:
            gazette: The gazette to get digests for

        Returns:
            List[DigestSchema]: List of published digests that match the gazette's criteria
        """
        # Start with base query for published digests from the same project
        query = (
            self.db.query(Digest)
            .filter(Digest.project_id == gazette.project_id)
            .filter(Digest.status == DigestStatuses.PUBLISHED)
        )

        # Apply tag filtering if gazette has tags
        if gazette.tags:
            # Use PostgreSQL array overlap operator for efficient tag matching
            query = query.filter(Digest.tags.overlap(gazette.tags))

        # Apply label filtering if gazette has labels
        if gazette.labels:
            # Use PostgreSQL JSONB contains operator for efficient label matching
            for key, value in gazette.labels.items():
                query = query.filter(Digest.labels[key].astext == str(value))

        # Execute query and convert to schemas
        digests = query.all()
        return [DigestSchema.model_validate(digest) for digest in digests]
