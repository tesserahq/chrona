from uuid import uuid4


def test_list_entry_updates(client, setup_entry_update):
    """Test GET /entries/{entry_id}/entry-updates endpoint."""
    entry_update = setup_entry_update
    entry_id = entry_update.entry_id

    response = client.get(f"/entries/{entry_id}/entry-updates")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1

    # Find our entry update in the response
    entry_update_found = False
    for item in data["data"]:
        if item["id"] == str(entry_update.id):
            entry_update_found = True
            assert item["body"] == entry_update.body
            assert item["source_author_id"] == str(entry_update.source_author_id)
            assert item["entry_id"] == str(entry_update.entry_id)
            break
    assert entry_update_found


def test_list_entry_updates_entry_not_found(client):
    """Test GET /entries/{entry_id}/entry-updates with non-existent entry."""
    fake_entry_id = uuid4()
    response = client.get(f"/entries/{fake_entry_id}/entry-updates")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_get_entry_update(client, setup_entry_update):
    """Test GET /entry-updates/{entry_update_id} endpoint."""
    entry_update = setup_entry_update

    response = client.get(f"/entry-updates/{entry_update.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(entry_update.id)
    assert data["body"] == entry_update.body
    assert data["source_author_id"] == str(entry_update.source_author_id)
    assert data["entry_id"] == str(entry_update.entry_id)


def test_get_entry_update_not_found(client):
    """Test GET /entry-updates/{entry_update_id} with non-existent entry update."""
    fake_entry_update_id = uuid4()

    response = client.get(f"/entry-updates/{fake_entry_update_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry update not found"


def test_create_entry_update(client, setup_source_author, setup_entry):
    """Test POST /entries/{entry_id}/entry-updates endpoint."""
    source_author = setup_source_author
    entry = setup_entry

    entry_update_data = {
        "body": "This is a test entry update",
        "source_author_id": str(source_author.id),
        "source_id": str(entry.source_id),
        "tags": ["feedback"],
        "labels": {"priority": "medium"},
        "meta_data": {"source": "test"},
        "entry_id": str(entry.id),
        "external_id": "test_external_id_123",
    }

    response = client.post(f"/entries/{entry.id}/entry-updates", json=entry_update_data)
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == entry_update_data["body"]
    assert data["source_author_id"] == str(source_author.id)
    assert data["entry_id"] == str(entry.id)
    assert "feedback" in data["tags"]
    assert data["labels"]["priority"] == "medium"


def test_create_entry_update_entry_not_found(client, setup_source_author):
    """Test POST /entries/{entry_id}/entry-updates with non-existent entry."""
    source_author = setup_source_author
    fake_entry_id = uuid4()

    entry_update_data = {
        "body": "This is a test entry update",
        "source_author_id": str(source_author.id),
    }

    response = client.post(
        f"/entries/{fake_entry_id}/entry-updates", json=entry_update_data
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_create_entry_update_invalid_data(client, setup_entry):
    """Test POST /entries/{entry_id}/entry-updates with invalid data."""
    entry = setup_entry

    invalid_data = {
        "body": "",  # Empty body should fail validation
    }

    response = client.post(f"/entries/{entry.id}/entry-updates", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_update_entry_update(client, setup_entry_update):
    """Test PUT /entry-updates/{entry_update_id} endpoint."""
    entry_update = setup_entry_update

    update_data = {
        "body": "Updated entry update body",
        "tags": ["updated", "modified"],
    }

    response = client.put(f"/entry-updates/{entry_update.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(entry_update.id)
    assert data["body"] == update_data["body"]
    assert "updated" in data["tags"]


def test_update_entry_update_not_found(client):
    """Test PUT /entry-updates/{entry_update_id} with non-existent entry update."""
    fake_entry_update_id = uuid4()

    update_data = {"body": "Updated entry update body"}

    response = client.put(f"/entry-updates/{fake_entry_update_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry update not found"


def test_delete_entry_update(client, setup_entry_update):
    """Test DELETE /entry-updates/{entry_update_id} endpoint."""
    entry_update = setup_entry_update

    response = client.delete(f"/entry-updates/{entry_update.id}")
    assert response.status_code == 204

    # Verify entry update is soft deleted (not found)
    get_response = client.get(f"/entry-updates/{entry_update.id}")
    assert get_response.status_code == 404


def test_delete_entry_update_not_found(client):
    """Test DELETE /entry-updates/{entry_update_id} with non-existent entry update."""
    fake_entry_update_id = uuid4()

    response = client.delete(f"/entry-updates/{fake_entry_update_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry update not found"


def test_list_entry_updates_pagination(client, setup_entry_update):
    """Test GET /entries/{entry_id}/entry-updates with pagination parameters."""
    entry_update = setup_entry_update
    entry_id = entry_update.entry_id

    # Test with skip and limit
    response = client.get(f"/entries/{entry_id}/entry-updates?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 1

    # Test with different pagination
    response = client.get(f"/entries/{entry_id}/entry-updates?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


def test_create_entry_update_auto_sets_entry_id(
    client, setup_source_author, setup_entry
):
    """Test that creating an entry update automatically sets the entry_id from the URL."""
    entry = setup_entry
    source_author = setup_source_author

    entry_update_data = {
        "body": "This is a test entry update",
        "source_author_id": str(source_author.id),
        "source_id": str(entry.source_id),
        "entry_id": str(entry.id),
        "external_id": "test_external_id_456",
        # Note: not providing entry_id in the request body
    }

    response = client.post(f"/entries/{entry.id}/entry-updates", json=entry_update_data)
    assert response.status_code == 201
    data = response.json()
    assert data["entry_id"] == str(entry.id)
    assert data["body"] == entry_update_data["body"]


def test_list_entry_updates_empty_entry(client, setup_entry):
    """Test GET /entries/{entry_id}/entry-updates for entry with no entry updates."""
    entry = setup_entry

    response = client.get(f"/entries/{entry.id}/entry-updates")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 0
