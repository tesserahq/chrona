from uuid import uuid4


def test_list_entries(client, setup_entry):
    """Test GET /entries endpoint."""
    entry = setup_entry

    response = client.get("/entries")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1

    # Find our entry in the response
    entry_found = False
    for item in data["data"]:
        if item["id"] == str(entry.id):
            entry_found = True
            assert item["title"] == entry.title
            assert item["body"] == entry.body
            assert item["author_id"] == str(entry.author_id)
            assert item["project_id"] == str(entry.project_id)
            break
    assert entry_found


def test_get_entry(client, setup_entry):
    """Test GET /entries/{entry_id} endpoint."""
    entry = setup_entry

    response = client.get(f"/entries/{entry.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(entry.id)
    assert data["title"] == entry.title
    assert data["body"] == entry.body
    assert data["author_id"] == str(entry.author_id)
    assert data["project_id"] == str(entry.project_id)


def test_get_entry_not_found(client):
    """Test GET /entries/{entry_id} with non-existent entry."""
    fake_id = uuid4()
    response = client.get(f"/entries/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_create_entry(client, setup_user, setup_project):
    """Test POST /entries endpoint."""
    user = setup_user
    project = setup_project

    entry_data = {
        "title": "Test Entry",
        "body": "This is a test entry body",
        "source": "test",
        "external_id": str(uuid4()),
        "tags": ["test", "example"],
        "labels": {"priority": "high"},
        "meta_data": {"created_by": "test"},
        "author_id": str(user.id),
        "project_id": str(project.id),
    }

    response = client.post("/entries", json=entry_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == entry_data["title"]
    assert data["body"] == entry_data["body"]
    assert data["author_id"] == str(user.id)
    assert data["project_id"] == str(project.id)
    assert "test" in data["tags"]
    assert data["labels"]["priority"] == "high"


def test_create_entry_invalid_data(client):
    """Test POST /entries with invalid data."""
    invalid_data = {
        "title": "",  # Empty title should fail validation
        "body": "Test body",
    }

    response = client.post("/entries", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_update_entry(client, setup_entry):
    """Test PUT /entries/{entry_id} endpoint."""
    entry = setup_entry

    update_data = {
        "title": "Updated Entry Title",
        "body": "Updated entry body",
        "tags": ["updated", "modified"],
    }

    response = client.put(f"/entries/{entry.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(entry.id)
    assert data["title"] == update_data["title"]
    assert data["body"] == update_data["body"]
    assert "updated" in data["tags"]


def test_update_entry_not_found(client):
    """Test PUT /entries/{entry_id} with non-existent entry."""
    fake_id = uuid4()
    update_data = {"title": "Updated Title"}

    response = client.put(f"/entries/{fake_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_delete_entry(client, setup_entry):
    """Test DELETE /entries/{entry_id} endpoint."""
    entry = setup_entry

    response = client.delete(f"/entries/{entry.id}")
    assert response.status_code == 204

    # Verify entry is soft deleted (not found)
    get_response = client.get(f"/entries/{entry.id}")
    assert get_response.status_code == 404


def test_delete_entry_not_found(client):
    """Test DELETE /entries/{entry_id} with non-existent entry."""
    fake_id = uuid4()
    response = client.delete(f"/entries/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_search_entries_exact_match(client, setup_entry):
    """Test POST /entries/search with exact match."""
    entry = setup_entry

    search_filters = {"title": entry.title}

    response = client.post("/entries/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    assert data["data"][0]["id"] == str(entry.id)


def test_search_entries_partial_match(client, setup_entry):
    """Test POST /entries/search with partial match using ilike."""
    entry = setup_entry
    partial_title = entry.title[: max(1, len(entry.title) // 2)]

    search_filters = {"title": {"operator": "ilike", "value": f"%{partial_title}%"}}

    response = client.post("/entries/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1


def test_search_entries_by_author(client, setup_entry):
    """Test POST /entries/search by author_id."""
    entry = setup_entry

    search_filters = {"author_id": str(entry.author_id)}

    response = client.post("/entries/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1


def test_search_entries_by_project(client, setup_entry):
    """Test POST /entries/search by project_id."""
    entry = setup_entry

    search_filters = {"project_id": str(entry.project_id)}

    response = client.post("/entries/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1


def test_search_entries_no_results(client):
    """Test POST /entries/search with filters that return no results."""
    search_filters = {"external_id": str(uuid4())}

    response = client.post("/entries/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 0


def test_list_entries_pagination(client, setup_entry):
    """Test GET /entries with pagination parameters."""
    entry = setup_entry

    # Test with skip and limit
    response = client.get("/entries?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 1

    # Test with different pagination
    response = client.get("/entries?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
