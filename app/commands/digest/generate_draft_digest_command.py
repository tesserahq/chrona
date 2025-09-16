from uuid import UUID
from sqlalchemy.orm import Session
from app.config import get_settings
from app.constants.digest_constants import DigestStatuses
from app.models.digest import Digest
from app.schemas.digest import DigestCreate
from app.services.digest_generation_config_service import DigestGenerationConfigService
from datetime import datetime, date
from app.utils.m2m_token import M2MTokenClient
from tessera_sdk import QuoreClient


class GenerateDraftDigestCommand:
    """Command to generate a draft digest for a digest generation config."""

    def __init__(self, db: Session):
        self.db = db
        self.digest_generation_config_service = DigestGenerationConfigService(db)

    def execute(self, digest_generation_config_id: UUID) -> Digest:
        """
        Execute the command to generate a draft digest.

        :param digest_generation_config_id: The ID of the digest generation config.
        :return: The created draft Digest object.
        """
        digest_generation_config = (
            self.digest_generation_config_service.get_digest_generation_config(
                digest_generation_config_id
            )
        )
        # Get entries and entry updates for the digest
        entries, entry_updates, config = (
            self.digest_generation_config_service.get_entries_for_digest(
                digest_generation_config_id
            )
        )
        entry_ids = [UUID(str(entry.id)) for entry in entries]
        entry_updates_ids = [UUID(str(update.id)) for update in entry_updates]
        today = date.today()
        formatted_body = self.digest_generation_config_service.format_digest_body(
            entries, entry_updates
        )

        m2m_token = self._get_m2m_token()

        quore_client = QuoreClient(
            base_url=get_settings().quore_api_url,
            timeout=60,  # Shorter timeout for middleware
            max_retries=1,  # Fewer retries for middleware
            api_token=m2m_token,
        )

        summary_response = quore_client.summarize(
            project_id="46421313-a8fe-4f81-97d5-25c24d3d25e1",
            prompt_id="summarize",
            text=formatted_body,
        )

        # Create the digest from the entries
        digest = self.digest_generation_config_service.create_draft_digest(
            DigestCreate(
                title=digest_generation_config.title,
                body=summary_response.summary,
                entries_ids=entry_ids,
                entry_updates_ids=entry_updates_ids,
                from_date=datetime.combine(today, datetime.min.time()),
                to_date=datetime.combine(today, datetime.max.time()),
                digest_generation_config_id=UUID(str(config.id)),
                project_id=UUID(str(config.project_id)),
                tags=list(config.tags) if config.tags else [],
                labels=dict(config.labels) if config.labels else {},
                status=DigestStatuses.DRAFT,
            )
        )

        return digest

    def _get_m2m_token(self) -> str:
        """
        Get an M2M token for Quore.
        """
        return M2MTokenClient().get_token_sync().access_token
