from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.constants.digest_constants import DigestStatuses
from app.models.digest import Digest
from app.schemas.digest import DigestCreate, DigestUpdate
from app.services.digest_generation_config_service import DigestGenerationConfigService
from datetime import datetime, date
from app.services.digest_service import DigestService
from app.services.project_service import ProjectService
from app.utils.m2m_token import M2MTokenClient
from app.utils.date_filter import calculate_digest_date_range
from tessera_sdk import QuoreClient  # type: ignore


class GenerateDraftDigestCommand:
    """Command to generate a draft digest for a digest generation config."""

    def __init__(self, db: Session):
        self.db = db
        self.digest_generation_config_service = DigestGenerationConfigService(db)
        self.digest_service = DigestService(db)

    def execute(
        self,
        digest_generation_config_id: UUID,
        execution_time: Optional[datetime] = None,
    ) -> Digest:
        """
        Execute the command to generate a draft digest.

        :param digest_generation_config_id: The ID of the digest generation config.
        :param execution_time: Time when the digest is being generated (defaults to now).
        :return: The created draft Digest object.
        """

        digest_generation_config = (
            self.digest_generation_config_service.get_digest_generation_config(
                digest_generation_config_id
            )
        )

        if not digest_generation_config:
            raise ValueError(
                f"Digest generation config with ID {digest_generation_config_id} not found"
            )

        # Calculate the date range based on cron expression and timezone
        from_date, to_date = calculate_digest_date_range(
            str(digest_generation_config.cron_expression),
            str(digest_generation_config.timezone),
            execution_time,
        )

        # Create the digest from the entries
        digest = self.digest_service.create_digest(
            DigestCreate(
                title=str(digest_generation_config.title),
                body="Generating...",
                raw_body="Generating...",
                from_date=from_date,
                to_date=to_date,
                digest_generation_config_id=UUID(str(digest_generation_config.id)),
                project_id=UUID(str(digest_generation_config.project_id)),
                status=DigestStatuses.GENGERATING,
            )
        )

        # Get entries and entry updates for the digest
        entries, entry_updates, config = (
            self.digest_generation_config_service.get_entries_for_digest(
                digest_generation_config_id, execution_time
            )
        )
        entry_ids = [UUID(str(entry.id)) for entry in entries]
        entry_updates_ids = [UUID(str(update.id)) for update in entry_updates]

        formatted_body = self.digest_generation_config_service.format_digest_body(
            entries, entry_updates
        )

        project = ProjectService(self.db).get_project(
            UUID(str(digest_generation_config.project_id))
        )
        raw_body = formatted_body
        summary = formatted_body

        if project and project.quore_project_id:
            m2m_token = self._get_m2m_token()

            quore_client = QuoreClient(
                base_url=get_settings().quore_api_url,
                timeout=60,  # Shorter timeout for middleware
                max_retries=1,  # Fewer retries for middleware
                api_token=m2m_token,
            )

            summary_response = quore_client.summarize(
                project_id=project.quore_project_id,
                prompt_id="summarize",
                # This could be part of the config.
                text=formatted_body,
                query="Summarize the tasks and their latest updates.",
            )
            summary = summary_response.summary

        updated_digest = self.digest_service.update_digest(
            UUID(str(digest.id)),
            DigestUpdate(
                title=str(digest_generation_config.title),
                project_id=UUID(str(digest_generation_config.project_id)),
                status=DigestStatuses.DRAFT,
                body=summary,
                raw_body=raw_body,
                entries_ids=entry_ids,
                entry_updates_ids=entry_updates_ids,
                from_date=from_date,
                to_date=to_date,
                tags=(
                    list(digest_generation_config.tags)
                    if digest_generation_config.tags
                    else []
                ),
                labels=(
                    dict(digest_generation_config.labels)
                    if digest_generation_config.labels
                    else {}
                ),
            ),
        )

        if not updated_digest:
            raise ValueError("Failed to update digest")

        return updated_digest

    def _get_m2m_token(self) -> str:
        """
        Get an M2M token for Quore.
        """
        return M2MTokenClient().get_token_sync().access_token
