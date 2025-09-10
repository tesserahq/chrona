from uuid import uuid4


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
