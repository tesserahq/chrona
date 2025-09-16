from uuid import uuid4
from sqlalchemy.orm import Session
import pytest

from app.services.gazette_service import GazetteService
from app.schemas.gazette import GazetteCreate, GazetteUpdate
from app.exceptions.resource_not_found_error import ResourceNotFoundError


def test_create_gazette(db: Session, setup_project, faker):
    """Test creating a new gazette."""
    project = setup_project
    service = GazetteService(db)

    gazette_in = GazetteCreate(
        header="Test Gazette Header",
        subheader="Test Subheader",
        theme="technology",
        tags=["tech", "news"],
        labels={"category": "weekly", "priority": 1},
        project_id=project.id,
        share_key="test-share-123",
    )

    gazette = service.create_gazette(gazette_in)

    assert gazette.id is not None
    assert gazette.header == "Test Gazette Header"
    assert gazette.subheader == "Test Subheader"
    assert gazette.theme == "technology"
    assert gazette.tags == ["tech", "news"]
    assert gazette.labels == {"category": "weekly", "priority": 1}
    assert gazette.project_id == project.id
    assert gazette.share_key == "test-share-123"


def test_create_gazette_minimal(db: Session, setup_project):
    """Test creating a gazette with only required fields."""
    project = setup_project
    service = GazetteService(db)

    gazette_in = GazetteCreate(header="Minimal Gazette", project_id=project.id)

    gazette = service.create_gazette(gazette_in)

    assert gazette.id is not None
    assert gazette.header == "Minimal Gazette"
    assert gazette.subheader is None
    assert gazette.theme is None
    assert gazette.tags == []
    assert gazette.labels == {}
    assert gazette.project_id == project.id
    assert gazette.share_key is None


def test_create_gazette_invalid_project(db: Session):
    """Test creating a gazette with non-existent project raises error."""
    service = GazetteService(db)
    fake_project_id = uuid4()

    gazette_in = GazetteCreate(header="Test Gazette", project_id=fake_project_id)

    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.create_gazette(gazette_in)

    assert f"Project with ID {fake_project_id} not found" in str(exc_info.value)


def test_get_gazette(db: Session, setup_gazette):
    """Test retrieving a gazette by ID."""
    service = GazetteService(db)
    gazette = setup_gazette

    retrieved_gazette = service.get_gazette(gazette.id)

    assert retrieved_gazette is not None
    assert retrieved_gazette.id == gazette.id
    assert retrieved_gazette.header == gazette.header
    assert retrieved_gazette.project_id == gazette.project_id


def test_get_gazette_not_found(db: Session):
    """Test retrieving a non-existent gazette returns None."""
    service = GazetteService(db)
    fake_id = uuid4()

    result = service.get_gazette(fake_id)

    assert result is None


def test_get_gazettes(db: Session, setup_gazette, setup_gazette_minimal):
    """Test retrieving gazettes with pagination."""
    service = GazetteService(db)
    gazette1 = setup_gazette
    gazette2 = setup_gazette_minimal

    # Get all gazettes
    gazettes = service.get_gazettes()

    assert len(gazettes) >= 2
    gazette_ids = [g.id for g in gazettes]
    assert gazette1.id in gazette_ids
    assert gazette2.id in gazette_ids

    # Test pagination
    gazettes_page1 = service.get_gazettes(skip=0, limit=1)
    assert len(gazettes_page1) == 1

    gazettes_page2 = service.get_gazettes(skip=1, limit=1)
    assert len(gazettes_page2) == 1

    # Ensure different gazettes on different pages
    assert gazettes_page1[0].id != gazettes_page2[0].id


def test_update_gazette(db: Session, setup_gazette):
    """Test updating a gazette."""
    service = GazetteService(db)
    gazette = setup_gazette

    update_data = GazetteUpdate(
        header="Updated Header", theme="updated_theme", tags=["updated", "tags"]
    )

    updated_gazette = service.update_gazette(gazette.id, update_data)

    assert updated_gazette is not None
    assert updated_gazette.header == "Updated Header"
    assert updated_gazette.theme == "updated_theme"
    assert updated_gazette.tags == ["updated", "tags"]
    # Unchanged fields should remain the same
    assert updated_gazette.subheader == gazette.subheader
    assert updated_gazette.project_id == gazette.project_id


def test_update_gazette_not_found(db: Session):
    """Test updating a non-existent gazette returns None."""
    service = GazetteService(db)
    fake_id = uuid4()

    update_data = GazetteUpdate(header="New Header")
    result = service.update_gazette(fake_id, update_data)

    assert result is None


def test_delete_gazette(db: Session, setup_gazette):
    """Test soft deleting a gazette."""
    service = GazetteService(db)
    gazette = setup_gazette

    result = service.delete_gazette(gazette.id)

    assert result is True

    # Verify gazette is soft deleted (not accessible via normal query)
    deleted_gazette = service.get_gazette(gazette.id)
    assert deleted_gazette is None


def test_delete_gazette_not_found(db: Session):
    """Test deleting a non-existent gazette returns False."""
    service = GazetteService(db)
    fake_id = uuid4()

    result = service.delete_gazette(fake_id)

    assert result is False


def test_get_gazettes_by_project(db: Session, setup_project, setup_gazette, faker):
    """Test getting gazettes filtered by project."""
    service = GazetteService(db)
    project = setup_project
    gazette1 = setup_gazette

    # Create another gazette for the same project
    gazette_data = {
        "header": faker.sentence(nb_words=4),
        "project_id": project.id,
    }
    from app.models.gazette import Gazette

    gazette2 = Gazette(**gazette_data)
    db.add(gazette2)
    db.commit()
    db.refresh(gazette2)

    # Get gazettes for the project
    project_gazettes = service.get_gazettes_by_project(project.id)

    assert len(project_gazettes) >= 2
    gazette_ids = [g.id for g in project_gazettes]
    assert gazette1.id in gazette_ids
    assert gazette2.id in gazette_ids

    # Test pagination
    page1 = service.get_gazettes_by_project(project.id, skip=0, limit=1)
    assert len(page1) == 1


def test_get_gazette_by_share_key(db: Session, setup_gazette_with_share_key):
    """Test getting a gazette by share key."""
    service = GazetteService(db)
    gazette = setup_gazette_with_share_key

    found_gazette = service.get_gazette_by_share_key("test-share-key-123")

    assert found_gazette is not None
    assert found_gazette.id == gazette.id
    assert found_gazette.share_key == "test-share-key-123"


def test_get_gazette_by_share_key_not_found(db: Session):
    """Test getting a gazette by non-existent share key returns None."""
    service = GazetteService(db)

    result = service.get_gazette_by_share_key("non-existent-key")

    assert result is None


def test_search_gazettes_exact_match(db: Session, setup_gazette):
    """Test searching gazettes with exact matches."""
    service = GazetteService(db)
    gazette = setup_gazette

    # Test exact header match
    results = service.search({"header": gazette.header})
    assert len(results) >= 1
    result_ids = [r.id for r in results]
    assert gazette.id in result_ids

    # Test exact project_id match
    results = service.search({"project_id": gazette.project_id})
    assert len(results) >= 1
    result_ids = [r.id for r in results]
    assert gazette.id in result_ids


def test_search_gazettes_partial_match(db: Session, setup_gazette):
    """Test searching gazettes with partial matches using ilike."""
    service = GazetteService(db)
    gazette = setup_gazette

    # Test partial header match
    partial_header = gazette.header[: len(gazette.header) // 2]
    results = service.search(
        {"header": {"operator": "ilike", "value": f"%{partial_header}%"}}
    )
    assert len(results) >= 1
    result_ids = [r.id for r in results]
    assert gazette.id in result_ids


def test_search_gazettes_multiple_conditions(db: Session, setup_gazette):
    """Test searching gazettes with multiple conditions."""
    service = GazetteService(db)
    gazette = setup_gazette

    # Test multiple conditions
    results = service.search(
        {
            "header": {"operator": "ilike", "value": f"%{gazette.header}%"},
            "project_id": gazette.project_id,
        }
    )
    assert len(results) >= 1
    result_ids = [r.id for r in results]
    assert gazette.id in result_ids


def test_search_gazettes_no_matches(db: Session):
    """Test searching gazettes with no matching results."""
    service = GazetteService(db)

    # Test non-existent header
    results = service.search({"header": "NonExistentGazetteHeader123"})
    assert len(results) == 0

    # Test non-existent project_id
    results = service.search({"project_id": uuid4()})
    assert len(results) == 0


def test_search_gazettes_case_insensitive(db: Session, setup_gazette):
    """Test searching gazettes with case-insensitive matches."""
    service = GazetteService(db)
    gazette = setup_gazette

    # Test case-insensitive header match
    results = service.search(
        {"header": {"operator": "ilike", "value": gazette.header.upper()}}
    )
    assert len(results) >= 1
    result_ids = [r.id for r in results]
    assert gazette.id in result_ids


def test_search_gazettes_by_theme(db: Session, setup_gazette):
    """Test searching gazettes by theme."""
    service = GazetteService(db)
    gazette = setup_gazette

    if gazette.theme:
        results = service.search({"theme": gazette.theme})
        assert len(results) >= 1
        result_ids = [r.id for r in results]
        assert gazette.id in result_ids


def test_search_gazettes_by_share_key(db: Session, setup_gazette_with_share_key):
    """Test searching gazettes by share key."""
    service = GazetteService(db)
    gazette = setup_gazette_with_share_key

    results = service.search({"share_key": gazette.share_key})
    assert len(results) == 1
    assert results[0].id == gazette.id


def test_generate_share_key(db: Session):
    """Test generating a share key."""
    service = GazetteService(db)

    # Test default length
    share_key = service.generate_share_key()
    assert isinstance(share_key, str)
    assert len(share_key) > 0
    # URL-safe base64 with 16 bytes should produce ~22 characters
    assert len(share_key) >= 20

    # Test custom length
    share_key_short = service.generate_share_key(length=8)
    assert isinstance(share_key_short, str)
    assert len(share_key_short) < len(share_key)

    # Test that generated keys are different
    share_key_2 = service.generate_share_key()
    assert share_key != share_key_2


def test_generate_unique_share_key(db: Session, setup_project):
    """Test generating a unique share key."""
    service = GazetteService(db)
    project = setup_project

    # Generate first unique key
    unique_key_1 = service.generate_unique_share_key()
    assert isinstance(unique_key_1, str)
    assert len(unique_key_1) > 0

    # Create a gazette with this key
    gazette_data = {
        "header": "Test Gazette",
        "project_id": project.id,
        "share_key": unique_key_1,
    }
    from app.models.gazette import Gazette

    gazette = Gazette(**gazette_data)
    db.add(gazette)
    db.commit()

    # Generate another unique key - should be different
    unique_key_2 = service.generate_unique_share_key()
    assert unique_key_1 != unique_key_2

    # Verify the second key doesn't exist in database
    existing = service.get_gazette_by_share_key(unique_key_2)
    assert existing is None


def test_generate_unique_share_key_collision_handling(
    db: Session, setup_project, monkeypatch
):
    """Test that generate_unique_share_key handles collisions properly."""
    service = GazetteService(db)
    project = setup_project

    # Mock generate_share_key to always return the same value initially
    call_count = 0
    original_generate = service.generate_share_key

    def mock_generate_share_key(length=16):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return "collision-key"
        return original_generate(length)

    monkeypatch.setattr(service, "generate_share_key", mock_generate_share_key)

    # Create a gazette with the collision key
    gazette_data = {
        "header": "Existing Gazette",
        "project_id": project.id,
        "share_key": "collision-key",
    }
    from app.models.gazette import Gazette

    gazette = Gazette(**gazette_data)
    db.add(gazette)
    db.commit()

    # This should handle the collision and generate a different key
    unique_key = service.generate_unique_share_key()
    assert unique_key != "collision-key"
    assert call_count >= 3  # Should have tried collision-key twice, then succeeded


def test_generate_unique_share_key_max_attempts_exceeded(
    db: Session, setup_project, monkeypatch
):
    """Test that generate_unique_share_key raises error after max attempts."""
    service = GazetteService(db)
    project = setup_project

    # Mock generate_share_key to always return the same collision value
    def mock_generate_share_key(length=16):
        return "always-collision"

    monkeypatch.setattr(service, "generate_share_key", mock_generate_share_key)

    # Create a gazette with the collision key
    gazette_data = {
        "header": "Existing Gazette",
        "project_id": project.id,
        "share_key": "always-collision",
    }
    from app.models.gazette import Gazette

    gazette = Gazette(**gazette_data)
    db.add(gazette)
    db.commit()

    # This should raise RuntimeError after max attempts
    with pytest.raises(RuntimeError) as exc_info:
        service.generate_unique_share_key(max_attempts=3)

    assert "Unable to generate unique share key after 3 attempts" in str(exc_info.value)


def test_generate_or_get_share_key_new(db: Session, setup_gazette_minimal):
    """Test generate_or_get_share_key for gazette without share key."""
    service = GazetteService(db)
    gazette = setup_gazette_minimal

    # Ensure gazette doesn't have a share key initially
    assert gazette.share_key is None

    updated_gazette = service.generate_or_get_share_key(gazette.id)

    assert updated_gazette.id == gazette.id
    assert updated_gazette.share_key is not None
    assert len(updated_gazette.share_key) > 10  # Should be a reasonable length

    # Verify it was persisted to database
    db_gazette = service.get_gazette(gazette.id)
    assert db_gazette.share_key == updated_gazette.share_key


def test_generate_or_get_share_key_existing(db: Session, setup_gazette_with_share_key):
    """Test generate_or_get_share_key for gazette with existing share key."""
    service = GazetteService(db)
    gazette = setup_gazette_with_share_key
    original_share_key = gazette.share_key

    updated_gazette = service.generate_or_get_share_key(gazette.id)

    assert updated_gazette.id == gazette.id
    assert updated_gazette.share_key == original_share_key  # Should be unchanged

    # Verify it wasn't changed in database
    db_gazette = service.get_gazette(gazette.id)
    assert db_gazette.share_key == original_share_key


def test_generate_or_get_share_key_nonexistent(db: Session):
    """Test generate_or_get_share_key with non-existent gazette."""
    service = GazetteService(db)
    fake_id = uuid4()

    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.generate_or_get_share_key(fake_id)

    assert f"Gazette with ID {fake_id} not found" in str(exc_info.value)


def test_regenerate_share_key_new(db: Session, setup_gazette_minimal):
    """Test regenerate_share_key for gazette without existing share key."""
    service = GazetteService(db)
    gazette = setup_gazette_minimal

    # Ensure gazette doesn't have a share key initially
    assert gazette.share_key is None

    updated_gazette = service.regenerate_share_key(gazette.id)

    assert updated_gazette.id == gazette.id
    assert updated_gazette.share_key is not None
    assert len(updated_gazette.share_key) > 10  # Should be a reasonable length

    # Verify it was persisted to database
    db_gazette = service.get_gazette(gazette.id)
    assert db_gazette.share_key == updated_gazette.share_key


def test_regenerate_share_key_existing(db: Session, setup_gazette_with_share_key):
    """Test regenerate_share_key for gazette with existing share key."""
    service = GazetteService(db)
    gazette = setup_gazette_with_share_key
    original_share_key = gazette.share_key

    updated_gazette = service.regenerate_share_key(gazette.id)

    assert updated_gazette.id == gazette.id
    assert updated_gazette.share_key is not None
    assert updated_gazette.share_key != original_share_key  # Should be different
    assert len(updated_gazette.share_key) > 10  # Should be a reasonable length

    # Verify it was changed in database
    db_gazette = service.get_gazette(gazette.id)
    assert db_gazette.share_key == updated_gazette.share_key
    assert db_gazette.share_key != original_share_key


def test_regenerate_share_key_nonexistent(db: Session):
    """Test regenerate_share_key with non-existent gazette."""
    service = GazetteService(db)
    fake_id = uuid4()

    with pytest.raises(ResourceNotFoundError) as exc_info:
        service.regenerate_share_key(fake_id)

    assert f"Gazette with ID {fake_id} not found" in str(exc_info.value)
