import pytest
from fastapi import HTTPException
from app.commands.gazette.get_gazette_with_digests_command import (
    GetGazetteWithDigestsCommand,
)
from app.schemas.gazette import GazetteWithSectionsAndDigests


class TestGetGazetteWithDigestsCommand:
    """Test suite for GetGazetteWithDigestsCommand."""

    def test_execute_success(self, db, setup_gazette_with_share_key):
        """Test executing command successfully returns gazette with digests."""
        gazette = setup_gazette_with_share_key
        command = GetGazetteWithDigestsCommand(db)

        result = command.execute(gazette.share_key)

        assert isinstance(result, GazetteWithSectionsAndDigests)
        assert result.gazette.id == gazette.id
        assert isinstance(result.digests, list)
        assert isinstance(result.sections, list)
        # Note: share_key is excluded from the Gazette schema for security reasons

    def test_execute_gazette_not_found(self, db):
        """Test executing command with non-existent share key raises HTTPException."""
        command = GetGazetteWithDigestsCommand(db)
        non_existent_share_key = "non-existent-key"

        with pytest.raises(HTTPException) as exc_info:
            command.execute(non_existent_share_key)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Gazette not found"

    def test_execute_with_digests_list(self, db, setup_gazette_with_share_key):
        """Test executing command returns gazette with digests list."""
        gazette = setup_gazette_with_share_key
        command = GetGazetteWithDigestsCommand(db)

        result = command.execute(gazette.share_key)

        assert isinstance(result, GazetteWithSectionsAndDigests)
        assert result.gazette.id == gazette.id
        assert isinstance(result.digests, list)
        assert isinstance(result.sections, list)
        # The digests list may be empty if no published digests match the gazette's criteria

    def test_execute_with_sections_structure(self, db, setup_gazette_with_share_key):
        """Test executing command returns proper sections structure."""
        gazette = setup_gazette_with_share_key
        command = GetGazetteWithDigestsCommand(db)

        result = command.execute(gazette.share_key)

        assert isinstance(result, GazetteWithSectionsAndDigests)
        assert result.gazette.id == gazette.id
        assert isinstance(result.digests, list)
        assert isinstance(result.sections, list)

        # Check that sections are properly structured (even if empty)
        for section_with_digests in result.sections:
            assert hasattr(section_with_digests, "section")
            assert hasattr(section_with_digests, "digests")
            assert isinstance(section_with_digests.digests, list)
