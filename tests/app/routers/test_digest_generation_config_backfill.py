import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytz
from fastapi import HTTPException
from uuid import uuid4

from app.routers.digest_generation_config import backfill_digests
from app.commands.digest.backfill_digests_command import BackfillResult
from app.schemas.digest import DigestBackfillRequest
from app.exceptions.resource_not_found_error import ResourceNotFoundError


class TestDigestGenerationConfigBackfillEndpoint:
    """Test suite for the digest generation config backfill endpoint."""

    def test_backfill_digests_success(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test successful backfill operation."""
        config = setup_digest_generation_config

        # Mock the backfill command
        with patch(
            "app.routers.digest_generation_config.BackfillDigestsCommand"
        ) as mock_command_class:
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
                created_digests=[mock_digest], skipped_count=2, failed_count=0
            )

            mock_command_instance = mock_command_class.return_value
            mock_command_instance.execute.return_value = mock_result

            # Create request
            request = DigestBackfillRequest(
                days=7,
                start_from_date=datetime(2023, 10, 15, 12, 0, 0, tzinfo=pytz.UTC),
            )

            # Call the endpoint function directly
            response = backfill_digests(
                backfill_request=request,
                digest_generation_config=config,
                db=db,
                current_user=setup_user,
            )

            assert response.created_count == 1
            assert response.skipped_count == 2
            assert response.failed_count == 0
            assert len(response.digests) == 1

    def test_backfill_digests_command_error(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test backfill when command raises an error."""
        config = setup_digest_generation_config

        with patch(
            "app.routers.digest_generation_config.BackfillDigestsCommand"
        ) as mock_command_class:
            mock_command_instance = mock_command_class.return_value
            mock_command_instance.execute.side_effect = ValueError(
                "Invalid cron expression"
            )

            request = DigestBackfillRequest(days=7)

            with pytest.raises(HTTPException) as exc_info:
                backfill_digests(
                    backfill_request=request,
                    digest_generation_config=config,
                    db=db,
                    current_user=setup_user,
                )

            assert exc_info.value.status_code == 400
            assert "Invalid cron expression" in str(exc_info.value.detail)

    def test_backfill_digests_without_start_date(
        self, setup_digest_generation_config, setup_user, db
    ):
        """Test backfill without specifying start_from_date."""
        config = setup_digest_generation_config

        with patch(
            "app.routers.digest_generation_config.BackfillDigestsCommand"
        ) as mock_command_class:
            mock_result = BackfillResult(
                created_digests=[], skipped_count=0, failed_count=0
            )

            mock_command_instance = mock_command_class.return_value
            mock_command_instance.execute.return_value = mock_result

            request = DigestBackfillRequest(days=3)

            response = backfill_digests(
                backfill_request=request,
                digest_generation_config=config,
                db=db,
                current_user=setup_user,
            )

            assert response.created_count == 0

            # Verify the command was called with None for start_from_date and default force=False
            mock_command_instance.execute.assert_called_once_with(
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

        with patch(
            "app.routers.digest_generation_config.BackfillDigestsCommand"
        ) as mock_command_class:
            mock_command_instance = mock_command_class.return_value
            mock_command_instance.execute.side_effect = ResourceNotFoundError(
                "Config not found"
            )

            request = DigestBackfillRequest(days=7)

            with pytest.raises(HTTPException) as exc_info:
                backfill_digests(
                    backfill_request=request,
                    digest_generation_config=config,
                    db=db,
                    current_user=setup_user,
                )

            assert exc_info.value.status_code == 404
            assert "Config not found" in str(exc_info.value.detail)
