from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.constants.digest_constants import DigestStatuses
from app.models.digest import Digest
from app.schemas.digest import DigestCreate, DigestUpdate
from app.schemas.digest_generation_config import DigestGenerationSettings
from app.services.digest_generation_config_service import DigestGenerationConfigService
from datetime import datetime
from app.services.digest_service import DigestService
from app.services.project_service import ProjectService
from app.utils.m2m_token import M2MTokenClient
from app.utils.date_filter import calculate_digest_date_range
from tessera_sdk import QuoreClient  # type: ignore
from app.core.logging_config import get_logger


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
        settings: Optional[DigestGenerationSettings] = None,
    ) -> Optional[Digest]:
        """
        Execute the command to generate a draft digest.

        :param digest_generation_config_id: The ID of the digest generation config.
        :param execution_time: Time when the digest is being generated (defaults to now).
        :param settings: Optional settings to override default generation behavior.
        :return: The created draft Digest object.
        """

        logger = get_logger()

        digest_generation_config = (
            self.digest_generation_config_service.get_digest_generation_config(
                digest_generation_config_id
            )
        )
        logger.info(f"Digest generation config: {digest_generation_config}")
        if not digest_generation_config:
            raise ValueError(
                f"Digest generation config with ID {digest_generation_config_id} not found"
            )

        # Determine date range: use settings if provided, otherwise calculate from cron
        if settings and settings.date_filter:
            from_date = settings.date_filter.from_date
            to_date = settings.date_filter.to_date
        elif settings and settings.from_last_digest:
            # Get the last digest for this config and use its created_at as start_date
            last_digest = (
                self.db.query(Digest)
                .filter(
                    Digest.digest_generation_config_id == digest_generation_config_id,
                    Digest.deleted_at.is_(None),
                )
                .order_by(Digest.created_at.desc())
                .first()
            )
            if last_digest:
                from_date = last_digest.created_at
                to_date = execution_time if execution_time else datetime.utcnow()
            else:
                raise ValueError(
                    f"No previous digest found for digest generation config {digest_generation_config_id}. "
                    "Cannot use from_last_digest option."
                )
        else:
            # Calculate the date range based on cron expression and timezone
            from_date, to_date = calculate_digest_date_range(
                str(digest_generation_config.cron_expression),
                str(digest_generation_config.timezone),
                execution_time,
            )

        # Get entries and entry updates for the digest
        entries, entry_updates, config = (
            self.digest_generation_config_service.get_entries_for_digest(
                digest_generation_config_id, execution_time, settings=settings
            )
        )
        entry_ids = [UUID(str(entry.id)) for entry in entries]
        entry_updates_ids = [UUID(str(update.id)) for update in entry_updates]

        logger.info(f"Number of entries: {len(entry_ids)}")
        logger.info(f"Number of entry updates: {len(entry_updates_ids)}")
        if len(entry_ids) == 0 and not digest_generation_config.generate_empty_digest:
            return None

        logger.info("Creating digest")
        # Create the digest from the entries
        digest = self.digest_service.create_digest(
            DigestCreate(
                title=str(digest_generation_config.title),
                body="",
                raw_body="",
                from_date=from_date,
                to_date=to_date,
                digest_generation_config_id=UUID(str(digest_generation_config.id)),
                project_id=UUID(str(digest_generation_config.project_id)),
                status=DigestStatuses.GENGERATING,
                tags=digest_generation_config.tags,
                labels=digest_generation_config.labels,
                ui_format=digest_generation_config.ui_format,
            ),
            created_at=execution_time,
        )

        formatted_body = self.digest_generation_config_service.format_digest_body(
            entries, entry_updates
        )

        project = ProjectService(self.db).get_project(
            UUID(str(digest_generation_config.project_id))
        )
        raw_body = formatted_body
        summary = formatted_body

        logger.info(f"Project: {project.id}")
        logger.info(f"Quore project ID: {project.quore_project_id}")
        if project and project.quore_project_id:
            m2m_token = self._get_m2m_token()

            quore_client = QuoreClient(
                base_url=get_settings().quore_api_url,
                # TODO: This is a temporary solution, we need to move this into jobs
                timeout=320,  # Shorter timeout for middleware
                max_retries=1,  # Fewer retries for middleware
                api_token=m2m_token,
            )

            summary_response = quore_client.summarize(
                project_id=project.quore_project_id,
                prompt_id=digest_generation_config.system_prompt,
                # This could be part of the config.
                text=formatted_body,
                query=digest_generation_config.query,
            )
            summary = summary_response.summary

        logger.info(f"Updating digest: {digest.id}")
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
