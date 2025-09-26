import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta
from app.constants.digest_constants import DigestStatuses


@pytest.fixture
def setup_source_and_author(db, setup_workspace, faker):
    """Create a test source and source author for entries."""
    from app.models.source import Source
    from app.models.author import Author
    from app.models.source_author import SourceAuthor

    # Create source
    source_data = {
        "name": faker.company(),
        "description": faker.text(100),
        "identifier": str(faker.uuid4()),
        "workspace_id": setup_workspace.id,
    }
    source = Source(**source_data)
    db.add(source)
    db.commit()
    db.refresh(source)

    # Create author
    author_data = {
        "display_name": faker.name(),
        "avatar_url": faker.url(),
        "email": faker.email(),
        "tags": ["test"],
        "labels": {"type": "user"},
        "meta_data": {"source": "test"},
        "workspace_id": setup_workspace.id,
    }
    author = Author(**author_data)
    db.add(author)
    db.commit()
    db.refresh(author)

    # Create source_author relationship
    source_author_data = {
        "author_id": author.id,
        "source_id": source.id,
        "source_author_id": str(faker.uuid4()),
    }
    source_author = SourceAuthor(**source_author_data)
    db.add(source_author)
    db.commit()
    db.refresh(source_author)

    return source, author, source_author


@pytest.fixture
def setup_test_entries(db, setup_source_and_author, setup_project, faker):
    """Create test entries for today with matching tags and labels."""
    source, author, source_author = setup_source_and_author
    today = date.today()

    entries = []
    for i in range(3):
        entry_data = {
            "title": f"Test Entry {i}",
            "body": f"Test body content for entry {i}",
            "source_id": source.id,
            "external_id": f"ext-{i}",
            "tags": ["metal-api", "vmass"],
            "labels": {"hola": "chau"},
            "meta_data": {},
            "source_author_id": source_author.id,
            "project_id": setup_project.id,
            "created_at": datetime.combine(today, datetime.min.time()),
        }

        from app.models.entry import Entry

        entry = Entry(**entry_data)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        entries.append(entry)

    return entries


@pytest.fixture
def setup_test_entry_updates(db, setup_test_entries, setup_source_and_author, faker):
    """Create test entry updates for the test entries."""
    source, author, source_author = setup_source_and_author
    entries = setup_test_entries
    now = datetime.now()

    entry_updates = []
    for i, entry in enumerate(entries):
        update_data = {
            "body": f"Latest update for entry {i}",
            "source_author_id": source_author.id,
            "entry_id": entry.id,
            "tags": [],
            "labels": {},
            "meta_data": {},
            "external_id": f"update-{i}",
            "source_id": source.id,
            "source_created_at": now,  # Set to current time so it's within the last 2 days
        }

        from app.models.entry_update import EntryUpdate

        entry_update = EntryUpdate(**update_data)
        db.add(entry_update)
        db.commit()
        db.refresh(entry_update)
        entry_updates.append(entry_update)

    return entry_updates


def test_list_digest_generation_configs(client, setup_digest_generation_config):
    """Test GET /projects/{project_id}/digest-generation-configs endpoint."""
    config = setup_digest_generation_config

    response = client.get(f"/projects/{config.project_id}/digest-generation-configs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert item["title"] == config.title
            assert item["system_prompt"] == config.system_prompt
            assert item["timezone"] == config.timezone
            assert item["project_id"] == str(config.project_id)
            assert item["generate_empty_digest"] == config.generate_empty_digest
            assert item["cron_expression"] == config.cron_expression
            break
    assert config_found


def test_get_digest_generation_config(client, setup_digest_generation_config):
    """Test GET /digest-generation-configs/{config_id} endpoint."""
    config = setup_digest_generation_config

    response = client.get(f"/digest-generation-configs/{config.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(config.id)
    assert data["title"] == config.title
    assert data["system_prompt"] == config.system_prompt
    assert data["timezone"] == config.timezone
    assert data["project_id"] == str(config.project_id)
    assert data["generate_empty_digest"] == config.generate_empty_digest
    assert data["cron_expression"] == config.cron_expression


def test_get_digest_generation_config_not_found(client):
    """Test GET /digest-generation-configs/{config_id} with non-existent config."""
    fake_id = uuid4()
    response = client.get(f"/digest-generation-configs/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest generation config not found"


def test_create_digest_generation_config(client, setup_project):
    """Test POST /projects/{project_id}/digest-generation-configs endpoint."""
    project = setup_project

    config_data = {
        "title": "Daily Digest Config",
        "filter_tags": ["metal-api", "vmass"],
        "filter_labels": {"priority": "high"},
        "tags": ["daily", "automated"],
        "labels": {"type": "digest"},
        "system_prompt": "Generate a daily digest of important updates",
        "timezone": "UTC",
        "generate_empty_digest": True,
        "cron_expression": "0 10 * * *",
        "query": "Generate a daily digest of important updates",
    }

    response = client.post(
        f"/projects/{project.id}/digest-generation-configs", json=config_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == config_data["title"]
    assert data["system_prompt"] == config_data["system_prompt"]
    assert data["timezone"] == config_data["timezone"]
    assert data["project_id"] == str(project.id)
    assert data["generate_empty_digest"] == config_data["generate_empty_digest"]
    assert data["cron_expression"] == config_data["cron_expression"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_update_digest_generation_config(client, setup_digest_generation_config):
    """Test PUT /digest-generation-configs/{config_id} endpoint."""
    config = setup_digest_generation_config

    update_data = {
        "title": "Updated Daily Digest Config",
        "timezone": "America/New_York",
        "generate_empty_digest": False,
    }

    response = client.put(f"/digest-generation-configs/{config.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(config.id)
    assert data["title"] == update_data["title"]
    assert data["timezone"] == update_data["timezone"]
    assert data["generate_empty_digest"] == update_data["generate_empty_digest"]
    # Other fields should remain unchanged
    assert data["system_prompt"] == config.system_prompt
    assert data["cron_expression"] == config.cron_expression


def test_update_digest_generation_config_not_found(client):
    """Test PUT /digest-generation-configs/{config_id} with non-existent config."""
    fake_id = uuid4()
    update_data = {"title": "Updated Title"}

    response = client.put(f"/digest-generation-configs/{fake_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest generation config not found"


def test_delete_digest_generation_config(client, setup_digest_generation_config):
    """Test DELETE /digest-generation-configs/{config_id} endpoint."""
    config = setup_digest_generation_config

    response = client.delete(f"/digest-generation-configs/{config.id}")
    assert response.status_code == 204

    # Verify it's deleted by trying to get it
    response = client.get(f"/digest-generation-configs/{config.id}")
    assert response.status_code == 404


def test_delete_digest_generation_config_not_found(client):
    """Test DELETE /digest-generation-configs/{config_id} with non-existent config."""
    fake_id = uuid4()

    response = client.delete(f"/digest-generation-configs/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest generation config not found"


def test_search_digest_generation_configs_exact_match(
    client, setup_digest_generation_config
):
    """Test POST /projects/{project_id}/digest-generation-configs/search with exact match."""
    config = setup_digest_generation_config
    search_filters = {"title": config.title, "project_id": str(config.project_id)}

    response = client.post(
        f"/projects/{config.project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert item["title"] == config.title
            break
    assert config_found


def test_search_digest_generation_configs_partial_match(
    client, setup_digest_generation_config
):
    """Test POST /projects/{project_id}/digest-generation-configs/search with partial match using ilike."""
    config = setup_digest_generation_config
    # Search for part of the config title
    partial_title = config.title[: max(1, len(config.title) // 2)]
    search_filters = {
        "title": {"operator": "ilike", "value": f"%{partial_title}%"},
        "project_id": str(config.project_id),
    }

    response = client.post(
        f"/projects/{config.project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert partial_title.lower() in item["title"].lower()
            break
    assert config_found


def test_search_digest_generation_configs_by_timezone(
    client, setup_digest_generation_config
):
    """Test POST /projects/{project_id}/digest-generation-configs/search by timezone."""
    config = setup_digest_generation_config
    search_filters = {
        "timezone": config.timezone,
        "project_id": str(config.project_id),
    }

    response = client.post(
        f"/projects/{config.project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert item["timezone"] == config.timezone
            break
    assert config_found


def test_search_digest_generation_configs_by_generate_empty_digest(
    client, setup_digest_generation_config
):
    """Test POST /projects/{project_id}/digest-generation-configs/search by generate_empty_digest flag."""
    config = setup_digest_generation_config
    search_filters = {
        "generate_empty_digest": config.generate_empty_digest,
        "project_id": str(config.project_id),
    }

    response = client.post(
        f"/projects/{config.project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert item["generate_empty_digest"] == config.generate_empty_digest
            break
    assert config_found


def test_search_digest_generation_configs_by_cron_expression(
    client, setup_digest_generation_config
):
    """Test POST /projects/{project_id}/digest-generation-configs/search by cron_expression."""
    config = setup_digest_generation_config
    search_filters = {
        "cron_expression": config.cron_expression,
        "project_id": str(config.project_id),
    }

    response = client.post(
        f"/projects/{config.project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert item["cron_expression"] == config.cron_expression
            break
    assert config_found


def test_search_digest_generation_configs_no_results(client, setup_project):
    """Test POST /projects/{project_id}/digest-generation-configs/search with filters that return no results."""
    project = setup_project
    search_filters = {"title": "NonExistentConfigTitle123"}

    response = client.post(
        f"/projects/{project.id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0


def test_search_digest_generation_configs_multiple_conditions(
    client, setup_digest_generation_config
):
    """Test POST /projects/{project_id}/digest-generation-configs/search with multiple search conditions."""
    config = setup_digest_generation_config
    search_filters = {
        "title": {"operator": "ilike", "value": f"%{config.title}%"},
        "timezone": config.timezone,
        "generate_empty_digest": config.generate_empty_digest,
        "project_id": str(config.project_id),
    }

    response = client.post(
        f"/projects/{config.project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our config in the response
    config_found = False
    for item in data["items"]:
        if item["id"] == str(config.id):
            config_found = True
            assert config.title.lower() in item["title"].lower()
            assert item["timezone"] == config.timezone
            assert item["generate_empty_digest"] == config.generate_empty_digest
            break
    assert config_found


def test_search_digest_generation_configs_invalid_project(client):
    """Test POST /projects/{project_id}/digest-generation-configs/search with non-existent project."""
    fake_project_id = uuid4()
    search_filters = {"title": "test"}

    response = client.post(
        f"/projects/{fake_project_id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_search_digest_generation_configs_invalid_operator(client, setup_project):
    """Test POST /projects/{project_id}/digest-generation-configs/search with invalid operator."""
    project = setup_project
    search_filters = {"title": {"operator": "invalid_operator", "value": "test"}}

    response = client.post(
        f"/projects/{project.id}/digest-generation-configs/search",
        json=search_filters,
    )
    # This should return 422 for validation error
    assert response.status_code == 422


def test_search_digest_generation_configs_empty_filters(client, setup_project):
    """Test POST /projects/{project_id}/digest-generation-configs/search with empty filters."""
    project = setup_project
    search_filters = {}

    response = client.post(
        f"/projects/{project.id}/digest-generation-configs/search",
        json=search_filters,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    # Should return all configs for the project (if any exist)


def test_generate_draft_digest(
    client, setup_digest_generation_config, setup_test_entries, setup_test_entry_updates
):
    """Test POST /digest-generation-configs/{config_id}/draft endpoint."""
    config = setup_digest_generation_config

    response = client.post(f"/digest-generation-configs/{config.id}/draft")
    assert response.status_code == 201
    data = response.json()

    # Verify the digest was created
    assert data["title"] == config.title
    assert data["status"] == DigestStatuses.DRAFT
    assert data["digest_generation_config_id"] == str(config.id)
    assert data["project_id"] == str(config.project_id)

    # Verify entries are included
    assert len(data["entries_ids"]) == len(setup_test_entries)
    assert set(data["entries_ids"]) == {str(entry.id) for entry in setup_test_entries}

    # Verify entry updates are included
    assert len(data["entry_updates_ids"]) == len(setup_test_entry_updates)
    assert set(data["entry_updates_ids"]) == {
        str(update.id) for update in setup_test_entry_updates
    }

    # Verify the digest body format
    assert "* Test Entry 0" in data["body"]
    assert "Test body content for entry 0" in data["body"]
    assert "Latest update: Latest update for entry 0" in data["body"]

    # Verify date range - should be within the last 2 days for daily cron
    today = date.today()
    yesterday = today - timedelta(days=1)
    from_date = datetime.fromisoformat(data["from_date"].replace("Z", "+00:00"))
    to_date = datetime.fromisoformat(data["to_date"].replace("Z", "+00:00"))

    # from_date should be either today or yesterday (depending on when the test runs vs cron schedule)
    # The cron runs at 10 AM UTC daily, so if we're before 10 AM, from_date would be yesterday
    assert from_date.date() in [today, yesterday]
    # to_date should be today (when the digest is being generated)
    assert to_date.date() == today


def test_generate_draft_digest_config_not_found(client):
    """Test POST /digest-generation-configs/{config_id}/draft with non-existent config."""
    fake_id = uuid4()
    response = client.post(f"/digest-generation-configs/{fake_id}/draft")
    assert response.status_code == 404
    assert "Digest generation config not found" in response.json()["detail"]


def test_generate_draft_digest_no_matching_entries(
    client, setup_digest_generation_config
):
    """Test POST /digest-generation-configs/{config_id}/draft when no entries match."""
    config = setup_digest_generation_config
    # Update config to not generate empty digests
    from app.services.digest_generation_config_service import (
        DigestGenerationConfigService,
    )
    from app.db import get_db

    db = next(get_db())
    service = DigestGenerationConfigService(db)
    config.generate_empty_digest = False
    service.db.commit()

    response = client.post(f"/digest-generation-configs/{config.id}/draft")
    assert response.status_code == 404
    assert "No entries found matching the criteria" in response.json()["detail"]


def test_generate_draft_digest_empty_digest_allowed(
    client, setup_digest_generation_config
):
    """Test POST /digest-generation-configs/{config_id}/draft when no entries match but empty digest is allowed."""
    config = setup_digest_generation_config
    # Ensure empty digest is allowed
    from app.services.digest_generation_config_service import (
        DigestGenerationConfigService,
    )
    from app.db import get_db

    db = next(get_db())
    service = DigestGenerationConfigService(db)
    config.generate_empty_digest = True
    service.db.commit()

    response = client.post(f"/digest-generation-configs/{config.id}/draft")
    assert response.status_code == 201
    data = response.json()

    # Verify the digest was created even with no entries
    assert data["title"] == config.title
    assert data["status"] == DigestStatuses.DRAFT
    assert len(data["entries_ids"]) == 0
    assert len(data["entry_updates_ids"]) == 0
    assert data["body"] == ""
