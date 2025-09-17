from typing import Optional, List, Dict, Any, cast
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.gazette_service import GazetteService
from app.services.digest_service import DigestService
from app.services.section_service import SectionService
from app.schemas.gazette import (
    GazetteWithSectionsAndDigests,
    Gazette,
)
from app.schemas.digest import Digest as DigestSchema
from app.schemas.section import Section as SectionSchema, SectionWithDigests
from app.constants.digest_constants import DigestStatuses


class GetGazetteWithDigestsCommand:
    """Command to get a gazette by share key along with its matching digests."""

    def __init__(self, db: Session):
        self.db = db
        self.gazette_service = GazetteService(db)
        self.digest_service = DigestService(db)
        self.section_service = SectionService(db)

    def execute(self, share_key: str) -> GazetteWithSectionsAndDigests:
        """
        Execute the command to get a gazette with its digests.

        :param share_key: The share key of the gazette to retrieve.
        :return: The GazetteWithSectionsAndDigests object containing gazette, its digests, and sections with their digests.
        :raises HTTPException: If gazette is not found.
        """
        # Get gazette by share key
        gazette = self.gazette_service.get_gazette_by_share_key(share_key)
        if not gazette:
            raise HTTPException(status_code=404, detail="Gazette not found")

        # Get filtered digests for this gazette using the new search function
        # Ensure we're passing the actual values, not SQLAlchemy column objects
        project_id: UUID = cast(UUID, gazette.project_id)
        tags: Optional[List[str]] = list(gazette.tags) if gazette.tags else None
        labels: Optional[Dict[str, Any]] = (
            dict(gazette.labels) if gazette.labels else None
        )

        digest_models = self.digest_service.search_digests(
            project_id=project_id,
            tags=tags,
            labels=labels,
            status=DigestStatuses.PUBLISHED,
        )

        # Convert to Pydantic schemas
        digests = [DigestSchema.model_validate(digest) for digest in digest_models]

        # Get sections for this gazette
        gazette_id: UUID = cast(UUID, gazette.id)
        section_models = self.section_service.get_sections_by_gazette(gazette_id)

        # For each section, get its associated digests
        sections_with_digests = []
        for section_model in section_models:
            # Get digests for this section using the same logic as for gazette
            section_project_id: UUID = cast(
                UUID, gazette.project_id
            )  # Sections use gazette's project
            section_tags: Optional[List[str]] = (
                list(section_model.tags) if section_model.tags else None
            )
            section_labels: Optional[Dict[str, Any]] = (
                dict(section_model.labels) if section_model.labels else None
            )

            section_digest_models = self.digest_service.search_digests(
                project_id=section_project_id,
                tags=section_tags,
                labels=section_labels,
                status=DigestStatuses.PUBLISHED,
            )

            # Convert section digests to Pydantic schemas
            section_digests = [
                DigestSchema.model_validate(digest) for digest in section_digest_models
            ]

            # Convert section to Pydantic schema
            section_schema = SectionSchema.model_validate(section_model)

            # Create SectionWithDigests
            section_with_digests = SectionWithDigests(
                section=section_schema, digests=section_digests
            )
            sections_with_digests.append(section_with_digests)

        # Convert the database model to Pydantic schema (excludes share_key for security)
        gazette_schema = Gazette.model_validate(gazette)

        return GazetteWithSectionsAndDigests(
            gazette=gazette_schema, digests=digests, sections=sections_with_digests
        )
