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
from app.schemas.digest import DigestWithEntries as DigestSchema
from app.schemas.section import Section as SectionSchema, SectionWithDigests
from app.constants.digest_constants import DigestStatuses


class GetGazetteWithDigestsCommand:
    """Command to get a gazette by share key along with its matching digests."""

    def __init__(self, db: Session):
        self.db = db
        self.gazette_service = GazetteService(db)
        self.digest_service = DigestService(db)
        self.section_service = SectionService(db)

    def _get_available_tags(self, gazette, sections) -> List[str]:
        """Get all available tags from gazette and its sections."""
        available_tags = set()

        # Add gazette tags
        if gazette.tags:
            available_tags.update(gazette.tags)

        # Add section tags
        for section in sections:
            if section.tags:
                available_tags.update(section.tags)

        return list(available_tags)

    def _validate_tag_filter(
        self, tag_filter: List[str], available_tags: List[str]
    ) -> None:
        """Validate that all requested tags exist in gazette or sections."""
        if not tag_filter:
            return

        available_tags_set = set(available_tags)
        invalid_tags = [tag for tag in tag_filter if tag not in available_tags_set]

        if invalid_tags:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tags: {', '.join(invalid_tags)}. Available tags: {', '.join(sorted(available_tags))}",
            )

    def execute(
        self, share_key: str, tag_filter: Optional[List[str]] = None
    ) -> GazetteWithSectionsAndDigests:
        """
        Execute the command to get a gazette with its digests.

        :param share_key: The share key of the gazette to retrieve.
        :param tag_filter: Optional list of tags to filter digests. If provided, only these tags will be used
                          to filter digests instead of all gazette/section tags. Tags must exist in the gazette or its sections.
        :return: The GazetteWithSectionsAndDigests object containing gazette, its digests, and sections with their digests.
        :raises HTTPException: If gazette is not found or if invalid tags are provided.
        """
        # Get gazette by share key
        gazette = self.gazette_service.get_gazette_by_share_key(share_key)
        if not gazette:
            raise HTTPException(status_code=404, detail="Gazette not found")

        # Get sections for this gazette first to validate tags
        gazette_id: UUID = cast(UUID, gazette.id)
        section_models = self.section_service.get_sections_by_gazette(gazette_id)

        # Validate tag filter if provided
        if tag_filter:
            available_tags = self._get_available_tags(gazette, section_models)
            self._validate_tag_filter(tag_filter, available_tags)

        # Get filtered digests for this gazette using the new search function
        # Ensure we're passing the actual values, not SQLAlchemy column objects
        project_id: UUID = cast(UUID, gazette.project_id)

        # Use tag_filter if provided, otherwise use gazette tags
        tags: Optional[List[str]] = (
            tag_filter if tag_filter else (list(gazette.tags) if gazette.tags else None)
        )
        labels: Optional[Dict[str, Any]] = (
            dict(gazette.labels) if gazette.labels else None
        )

        digest_models = self.digest_service.search_digests(
            project_id=project_id,
            tags=tags,
            labels=labels,
            status=DigestStatuses.PUBLISHED,
        )

        # Convert to Pydantic schemas with entries
        digests = []
        for digest_model in digest_models:
            digest_id: UUID = cast(UUID, digest_model.id)
            digest_with_entries = self.digest_service.get_digest_with_entries(digest_id)
            if digest_with_entries:
                digests.append(DigestSchema.model_validate(digest_with_entries))

        # For each section, get its associated digests
        sections_with_digests = []
        for section_model in section_models:
            # Get digests for this section using the same logic as for gazette
            section_project_id: UUID = cast(
                UUID, gazette.project_id
            )  # Sections use gazette's project

            # Use tag_filter if provided, otherwise use section tags
            section_tags: Optional[List[str]] = (
                tag_filter
                if tag_filter
                else (list(section_model.tags) if section_model.tags else None)
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

            # Convert section digests to Pydantic schemas with entries
            section_digests = []
            for digest_model in section_digest_models:
                section_digest_id: UUID = cast(UUID, digest_model.id)
                digest_with_entries = self.digest_service.get_digest_with_entries(
                    section_digest_id
                )
                if digest_with_entries:
                    section_digests.append(
                        DigestSchema.model_validate(digest_with_entries)
                    )

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
