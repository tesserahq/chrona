from uuid import UUID
from datetime import datetime
from typing import Optional

from app.db import SessionLocal
from app.core.celery_app import celery_app

# Import heavy dependencies only when task executes (lazy loading)
from app.commands.digest.backfill_digests_command import BackfillDigestsCommand
from app.core.logging_config import get_logger


@celery_app.task
def backfill_digests_task(
    digest_generation_config_id: str,
    days: int,
    start_from_date: Optional[str] = None,
    force: bool = False,
) -> dict:
    """
    Backfill digests for a digest generation config.
    This is an async task that runs in the background.

    Args:
        digest_generation_config_id: UUID string of the digest generation config
        days: Number of days to backfill
        start_from_date: Optional ISO format datetime string to start from
        force: Whether to force generation even if digests exists

    Returns:
        dict: Contains created_count, skipped_count, failed_count, deleted_count
    """
    logger = get_logger("chrona.tasks.backfill_digests")
    logger.info(
        f"Starting backfill task for {digest_generation_config_id} with {days} days"
    )
    db = SessionLocal()
    try:
        try:
            # Convert string ID to UUID with validation
            try:
                config_id = UUID(digest_generation_config_id)
            except ValueError as e:
                raise ValueError(
                    f"Invalid digest_generation_config_id format: {digest_generation_config_id}. Must be a valid UUID."
                ) from e

            # Parse start_from_date if provided
            parsed_start_date = None
            if start_from_date:
                try:
                    parsed_start_date = datetime.fromisoformat(
                        start_from_date.replace("Z", "+00:00")
                    )
                except ValueError as e:
                    raise ValueError(
                        f"Invalid start_from_date format: {start_from_date}. Must be ISO format."
                    ) from e

            logger.info(f"Parsed start date: {parsed_start_date}")
            # Execute the backfill command
            command = BackfillDigestsCommand(db)
            logger.info(f"Executing backfill command for {config_id} with {days} days")
            result = command.execute(
                digest_generation_config_id=config_id,
                days=days,
                start_from_date=parsed_start_date,
                force=force,
            )
            logger.info(f"Backfill command result: {result}")
            # Return serializable result
            return {
                "created_count": len(result.created_digests),
                "skipped_count": result.skipped_count,
                "failed_count": result.failed_count,
                "deleted_count": result.deleted_count,
                "digest_ids": [
                    str(digest.id) for digest in result.created_digests if digest.id
                ],
            }

        except Exception as e:
            raise RuntimeError(f"Failed to backfill digests: {str(e)}")
        finally:
            db.commit()
    finally:
        db.close()
