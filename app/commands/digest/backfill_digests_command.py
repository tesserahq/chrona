from uuid import UUID
from typing import List, Optional, NamedTuple, cast
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pytz  # type: ignore
from app.models.digest import Digest
from app.services.digest_generation_config_service import DigestGenerationConfigService
from app.commands.digest.generate_draft_digest_command import GenerateDraftDigestCommand
from crontab import CronTab  # type: ignore


class BackfillResult(NamedTuple):
    """Result of backfill operation."""

    created_digests: List[Digest]
    skipped_count: int
    failed_count: int
    deleted_count: int


class BackfillDigestsCommand:
    """Command to backfill digests for a digest generation config over a specified number of days."""

    def __init__(self, db: Session):
        self.db = db
        self.digest_generation_config_service = DigestGenerationConfigService(db)
        self.generate_draft_digest_command = GenerateDraftDigestCommand(db)

    def execute(
        self,
        digest_generation_config_id: UUID,
        days: int,
        start_from_date: Optional[datetime] = None,
        force: bool = False,
    ) -> BackfillResult:
        """
        Execute the command to backfill digests for the specified number of days.

        :param digest_generation_config_id: The ID of the digest generation config.
        :param days: Number of days to backfill digests for.
        :param start_from_date: Date to start backfilling from (defaults to now).
        :param force: If True, delete existing overlapping digests and create new ones (defaults to False).
        :return: BackfillResult with created digests, skipped count, failed count, and deleted count.
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

        # Use provided start date or default to now
        actual_start_date = (
            start_from_date if start_from_date is not None else datetime.now()
        )

        # Parse timezone
        try:
            tz = pytz.timezone(str(digest_generation_config.timezone))
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC

        # Ensure start_from_date is timezone-aware
        if actual_start_date.tzinfo is None:
            actual_start_date = pytz.UTC.localize(actual_start_date)

        start_from_date_tz = actual_start_date.astimezone(tz)

        # Parse cron expression to determine execution times
        cron_expression = str(digest_generation_config.cron_expression)

        try:
            cron = CronTab(cron_expression)
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{cron_expression}': {str(e)}")

        # Calculate execution times for backfill
        execution_times = self._calculate_execution_times(
            cron, start_from_date_tz, days
        )

        created_digests = []
        skipped_count = 0
        failed_count = 0
        deleted_count = 0

        # Generate digests for each execution time
        for execution_time in execution_times:
            try:
                if force:
                    # When force is True, delete any existing overlapping digests first
                    deleted_in_period = self._delete_overlapping_digests(
                        digest_generation_config_id, execution_time
                    )
                    deleted_count += deleted_in_period

                    # Create the new digest
                    digest = self.generate_draft_digest_command.execute(
                        digest_generation_config_id, execution_time
                    )
                    if digest:
                        created_digests.append(digest)
                        print(
                            f"Created digest for {execution_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (forced)"
                        )
                    else:
                        failed_count += 1
                        print(
                            f"Failed to create digest for {execution_time.strftime('%Y-%m-%d %H:%M:%S %Z')}: digest creation returned None"
                        )
                elif not self._digest_exists_for_time_period(
                    digest_generation_config_id, execution_time
                ):
                    # Normal case: create digest if it doesn't exist
                    digest = self.generate_draft_digest_command.execute(
                        digest_generation_config_id, execution_time
                    )
                    if digest:
                        created_digests.append(digest)
                        print(
                            f"Created digest for {execution_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                        )
                    else:
                        failed_count += 1
                        print(
                            f"Failed to create digest for {execution_time.strftime('%Y-%m-%d %H:%M:%S %Z')}: digest creation returned None"
                        )
                else:
                    skipped_count += 1
                    print(
                        f"Digest already exists for {execution_time.strftime('%Y-%m-%d %H:%M:%S %Z')}, skipping"
                    )

            except Exception as e:
                failed_count += 1
                print(
                    f"Failed to create digest for {execution_time.strftime('%Y-%m-%d %H:%M:%S %Z')}: {str(e)}"
                )
                continue

        return BackfillResult(
            created_digests=created_digests,
            skipped_count=skipped_count,
            failed_count=failed_count,
            deleted_count=deleted_count,
        )

    def _calculate_execution_times(
        self, cron: CronTab, start_from_date: datetime, days: int
    ) -> List[datetime]:
        """
        Calculate all execution times within the specified number of days based on cron expression.
        Uses a simple approach that works backwards from start_from_date.

        :param cron: Parsed CronTab object.
        :param start_from_date: Starting date in the target timezone.
        :param days: Number of days to look back.
        :return: List of execution times in chronological order.
        """
        execution_times = []

        # Calculate the end date (days ago from start_from_date)
        end_date = start_from_date - timedelta(days=days)

        # Simple approach: go back from start_from_date and find previous executions
        current_time = start_from_date

        # Use the cron library to find previous execution times
        while current_time > end_date:
            try:
                # Convert to naive datetime to work around cron library timezone bug
                # The cron library has issues with timezone-aware timestamps when default_utc=True
                if current_time.tzinfo is not None:
                    current_time_naive = current_time.replace(tzinfo=None)
                else:
                    current_time_naive = current_time

                # Get seconds until previous execution from current time
                prev_seconds = cron.previous(
                    now=current_time_naive.timestamp(), default_utc=False
                )

                # Calculate the actual previous execution time
                prev_execution_time = current_time - timedelta(
                    seconds=abs(prev_seconds)
                )

                # If this execution time is within our range, add it
                if prev_execution_time >= end_date:
                    execution_times.append(prev_execution_time)
                    # Move to just before this execution time to find the next previous one
                    current_time = prev_execution_time - timedelta(minutes=1)
                else:
                    break

            except Exception:
                # If cron calculation fails, move back by a day and try again
                current_time = current_time - timedelta(days=1)

        # Return in chronological order (oldest first)
        return sorted(execution_times)

    def _matches_cron_pattern(self, cron: CronTab, check_time: datetime) -> bool:
        """
        Check if a given datetime matches the cron pattern.

        :param cron: Parsed CronTab object.
        :param check_time: Time to check against the cron pattern.
        :return: True if the time matches the cron pattern.
        """
        return self._matches_cron_pattern_simple(cron, check_time)

    def _matches_cron_pattern_simple(self, cron: CronTab, check_time: datetime) -> bool:
        """
        Simple cron pattern matching using the crontab library's test method.

        :param cron: Parsed CronTab object.
        :param check_time: Time to check against the cron pattern.
        :return: True if the time matches the cron pattern.
        """
        try:
            # Convert to naive datetime to work around cron library timezone bug
            if check_time.tzinfo is not None:
                check_time_naive = check_time.replace(tzinfo=None)
            else:
                check_time_naive = check_time

            # Use the crontab library's test method to check if time matches
            # Convert datetime to timestamp for testing
            timestamp = check_time_naive.timestamp()

            # Get the time difference to the previous execution
            # The previous() method returns the number of seconds since the last execution
            prev_seconds = cron.previous(now=timestamp, default_utc=False)

            # If the previous execution was very recent (within 60 seconds), it's a match
            return abs(prev_seconds) <= 60

        except Exception:
            return False

    def _delete_overlapping_digests(
        self, digest_generation_config_id: UUID, execution_time: datetime
    ) -> int:
        """
        Delete any existing digests that overlap with the time period for the given execution time.

        :param digest_generation_config_id: The digest generation config ID.
        :param execution_time: The execution time to check.
        :return: Number of digests deleted.
        """
        # Import here to avoid circular imports
        from app.utils.date_filter import calculate_digest_date_range
        from app.services.digest_service import DigestService

        digest_service = DigestService(self.db)

        # Get the digest generation config to access cron expression and timezone
        config = self.digest_generation_config_service.get_digest_generation_config(
            digest_generation_config_id
        )

        if not config:
            return 0

        # Calculate what the date range would be for this execution time
        from_date, to_date = calculate_digest_date_range(
            str(config.cron_expression),
            str(config.timezone),
            execution_time,
        )

        # Find all digests that overlap with this time period
        existing_digests = digest_service.get_digests_by_config(
            digest_generation_config_id
        )

        deleted_count = 0
        for digest in existing_digests:
            if digest.from_date and digest.to_date:
                # Ensure both dates are timezone-aware for comparison
                digest_from = digest.from_date
                digest_to = digest.to_date

                if digest_from.tzinfo is None:
                    digest_from = pytz.UTC.localize(digest_from)
                if digest_to.tzinfo is None:
                    digest_to = pytz.UTC.localize(digest_to)

                # Check for overlap
                if digest_from <= to_date and digest_to >= from_date:
                    # Delete the overlapping digest
                    if digest.id:
                        digest_service.delete_digest(cast(UUID, digest.id))
                        deleted_count += 1
                        print(
                            f"Deleted existing digest for period {digest_from.strftime('%Y-%m-%d %H:%M:%S %Z')} to {digest_to.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                        )

        return deleted_count

    def _digest_exists_for_time_period(
        self, digest_generation_config_id: UUID, execution_time: datetime
    ) -> bool:
        """
        Check if a digest already exists for the time period that would be covered
        by generating a digest at the given execution time.

        :param digest_generation_config_id: The digest generation config ID.
        :param execution_time: The execution time to check.
        :return: True if a digest already exists for this time period.
        """
        # Import here to avoid circular imports
        from app.utils.date_filter import calculate_digest_date_range
        from app.services.digest_service import DigestService

        digest_service = DigestService(self.db)

        # Get the digest generation config to access cron expression and timezone
        config = self.digest_generation_config_service.get_digest_generation_config(
            digest_generation_config_id
        )

        if not config:
            return False

        # Calculate what the date range would be for this execution time
        from_date, to_date = calculate_digest_date_range(
            str(config.cron_expression),
            str(config.timezone),
            execution_time,
        )

        # Check if any digest exists for this config with overlapping date range
        existing_digests = digest_service.get_digests_by_config(
            digest_generation_config_id
        )

        for digest in existing_digests:
            if digest.from_date and digest.to_date:
                # Ensure both dates are timezone-aware for comparison
                digest_from = digest.from_date
                digest_to = digest.to_date

                if digest_from.tzinfo is None:
                    digest_from = pytz.UTC.localize(digest_from)
                if digest_to.tzinfo is None:
                    digest_to = pytz.UTC.localize(digest_to)

                # Check for overlap
                if digest_from <= to_date and digest_to >= from_date:
                    return True

        return False
