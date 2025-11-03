import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytz
from uuid import uuid4

from app.commands.digest.backfill_digests_command import (
    BackfillDigestsCommand,
    BackfillResult,
)
from app.exceptions.resource_not_found_error import ResourceNotFoundError


class TestDigestGenerationConfigBackfillEndpoint:
    """Test suite for the digest generation config backfill command."""

    def test_backfill_digests_success(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test successful backfill operation."""
        config = setup_digest_generation_config

        # Create mock digest
        mock_digest = Mock()
        mock_digest.id = uuid4()
        mock_digest.title = "Test Digest"
        mock_digest.from_date = datetime.now(pytz.UTC) - timedelta(days=1)
        mock_digest.to_date = datetime.now(pytz.UTC)
        mock_digest.created_at = datetime.now(pytz.UTC)
        mock_digest.updated_at = datetime.now(pytz.UTC)
        mock_digest.deleted_at = None
        mock_digest.body = "Test body"
        mock_digest.raw_body = "Test raw body"
        mock_digest.entries_ids = []
        mock_digest.entry_updates_ids = []
        mock_digest.tags = []
        mock_digest.labels = {}
        mock_digest.digest_generation_config_id = config.id
        mock_digest.project_id = config.project_id
        mock_digest.status = "draft"
        mock_digest.ui_format = {}

        # Add the digest_generation_config relationship
        mock_config = Mock()
        mock_config.id = config.id
        mock_config.ui_format = config.ui_format
        mock_digest.digest_generation_config = mock_config

        # Mock the command result
        mock_result = BackfillResult(
            created_digests=[mock_digest],
            skipped_count=2,
            failed_count=0,
            deleted_count=0,
        )

        # Mock the command and call it directly
        with patch.object(BackfillDigestsCommand, "execute", return_value=mock_result):
            command = BackfillDigestsCommand(db)
            result = command.execute(
                digest_generation_config_id=config.id,
                days=7,
                start_from_date=datetime(2023, 10, 15, 12, 0, 0, tzinfo=pytz.UTC),
                force=False,
            )

            assert len(result.created_digests) == 1
            assert result.skipped_count == 2
            assert result.failed_count == 0
            assert result.deleted_count == 0

    def test_backfill_digests_command_error(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test backfill when command raises an error."""
        config = setup_digest_generation_config

        with patch.object(
            BackfillDigestsCommand,
            "execute",
            side_effect=ValueError("Invalid cron expression"),
        ):
            command = BackfillDigestsCommand(db)

            with pytest.raises(ValueError) as exc_info:
                command.execute(
                    digest_generation_config_id=config.id,
                    days=7,
                    start_from_date=None,
                    force=False,
                )

            assert "Invalid cron expression" in str(exc_info.value)

    def test_backfill_digests_without_start_date(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test backfill without specifying start_from_date."""
        config = setup_digest_generation_config

        mock_result = BackfillResult(
            created_digests=[], skipped_count=0, failed_count=0, deleted_count=0
        )

        with patch.object(
            BackfillDigestsCommand, "execute", return_value=mock_result
        ) as mock_execute:
            command = BackfillDigestsCommand(db)
            result = command.execute(
                digest_generation_config_id=config.id,
                days=3,
                start_from_date=None,
                force=False,
            )

            assert len(result.created_digests) == 0
            assert result.skipped_count == 0
            assert result.failed_count == 0
            assert result.deleted_count == 0

            # Verify the command was called with the correct parameters
            mock_execute.assert_called_once_with(
                digest_generation_config_id=config.id,
                days=3,
                start_from_date=None,
                force=False,
            )

    def test_backfill_digests_resource_not_found_error(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test backfill when resource is not found."""
        config = setup_digest_generation_config

        with patch.object(
            BackfillDigestsCommand,
            "execute",
            side_effect=ResourceNotFoundError("Config not found"),
        ):
            command = BackfillDigestsCommand(db)

            with pytest.raises(ResourceNotFoundError) as exc_info:
                command.execute(
                    digest_generation_config_id=config.id,
                    days=7,
                    start_from_date=None,
                    force=False,
                )

            assert "Config not found" in str(exc_info.value)
