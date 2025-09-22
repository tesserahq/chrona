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

    def test_execute_with_valid_tag_filter(self, db, setup_gazette_with_share_key):
        """Test executing command with valid tag filter."""
        gazette = setup_gazette_with_share_key

        # Set some tags on the gazette
        gazette.tags = ["tag1", "tag2", "tag3"]
        db.commit()

        command = GetGazetteWithDigestsCommand(db)

        # Test with subset of valid tags
        result = command.execute(gazette.share_key, tag_filter=["tag1", "tag2"])

        assert isinstance(result, GazetteWithSectionsAndDigests)
        assert result.gazette.id == gazette.id

    def test_execute_with_invalid_tag_filter(self, db, setup_gazette_with_share_key):
        """Test executing command with invalid tag filter raises HTTPException."""
        gazette = setup_gazette_with_share_key

        # Set some tags on the gazette
        gazette.tags = ["tag1", "tag2", "tag3"]
        db.commit()

        command = GetGazetteWithDigestsCommand(db)

        # Test with invalid tags
        with pytest.raises(HTTPException) as exc_info:
            command.execute(gazette.share_key, tag_filter=["invalid_tag"])

        assert exc_info.value.status_code == 400
        assert "Invalid tags: invalid_tag" in exc_info.value.detail
        assert "Available tags:" in exc_info.value.detail

    def test_execute_with_empty_tag_filter(self, db, setup_gazette_with_share_key):
        """Test executing command with empty tag filter works like no filter."""
        gazette = setup_gazette_with_share_key
        command = GetGazetteWithDigestsCommand(db)

        # Test with empty tag filter
        result = command.execute(gazette.share_key, tag_filter=[])

        assert isinstance(result, GazetteWithSectionsAndDigests)
        assert result.gazette.id == gazette.id
