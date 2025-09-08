from uuid import uuid4


def test_list_entries(client, setup_entry):
    """Test GET /projects/{project_id}/entries endpoint."""
    entry = setup_entry

    response = client.get(f"/projects/{entry.project_id}/entries")
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
            assert item["source_author_id"] == str(entry.source_author_id)
            assert item["project_id"] == str(entry.project_id)
            # Check that source information is included
            assert "source" in item
            assert item["source"] is not None
            assert item["source"]["id"] == str(entry.source.id)
            assert item["source"]["name"] == entry.source.name
            # Check that source_author and author information is included
            assert "source_author" in item
            assert item["source_author"] is not None
            assert item["source_author"]["id"] == str(entry.source_author.id)
            assert (
                item["source_author"]["source_author_id"]
                == entry.source_author.source_author_id
            )
            # Check that author information is included within source_author
            assert "author" in item["source_author"]
            assert item["source_author"]["author"] is not None
            assert item["source_author"]["author"]["id"] == str(
                entry.source_author.author.id
            )
            assert (
                item["source_author"]["author"]["display_name"]
                == entry.source_author.author.display_name
            )
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
    assert data["source_author_id"] == str(entry.source_author_id)
    assert data["project_id"] == str(entry.project_id)
    # Check that source information is included
    assert "source" in data
    assert data["source"] is not None
    assert data["source"]["id"] == str(entry.source.id)
    assert data["source"]["name"] == entry.source.name
    # Check that source_author and author information is included
    assert "source_author" in data
    assert data["source_author"] is not None
    assert data["source_author"]["id"] == str(entry.source_author.id)
    assert (
        data["source_author"]["source_author_id"]
        == entry.source_author.source_author_id
    )
    # Check that author information is included within source_author
    assert "author" in data["source_author"]
    assert data["source_author"]["author"] is not None
    assert data["source_author"]["author"]["id"] == str(entry.source_author.author.id)
    assert (
        data["source_author"]["author"]["display_name"]
        == entry.source_author.author.display_name
    )


def test_get_entry_not_found(client):
    """Test GET /entries/{entry_id} with non-existent entry."""
    fake_id = uuid4()
    response = client.get(f"/entries/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_create_entry(client, setup_project, setup_source, setup_source_author):
    """Test POST /projects/{project_id}/entries endpoint."""
    project = setup_project
    source = setup_source
    source_author = setup_source_author

    entry_data = {
        "title": "Test Entry",
        "body": "This is a test entry body",
        "source_id": str(source.id),
        "external_id": str(uuid4()),
        "tags": ["test", "example"],
        "labels": {"priority": "high"},
        "meta_data": {"created_by": "test"},
        "source_author_id": str(source_author.id),
    }

    response = client.post(f"/projects/{project.id}/entries", json=entry_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == entry_data["title"]
    assert data["body"] == entry_data["body"]
    assert data["source_author_id"] == str(source_author.id)
    assert data["project_id"] == str(project.id)
    assert "test" in data["tags"]
    assert data["labels"]["priority"] == "high"
    # Check that source information is included
    assert "source" in data
    assert data["source"] is not None
    assert data["source"]["id"] == str(source.id)
    assert data["source"]["name"] == source.name
    # Check that source_author and author information is included
    assert "source_author" in data
    assert data["source_author"] is not None
    assert data["source_author"]["source_author_id"] == source_author.source_author_id
    # Check that author information is included within source_author
    assert "author" in data["source_author"]
    assert data["source_author"]["author"] is not None
    assert data["source_author"]["author"]["id"] == str(source_author.author.id)
    assert (
        data["source_author"]["author"]["display_name"]
        == source_author.author.display_name
    )


def test_create_entry_invalid_data(client, setup_project):
    """Test POST /projects/{project_id}/entries with invalid data."""
    project = setup_project
    invalid_data = {
        "title": "",  # Empty title should fail validation
        "body": "Test body",
    }

    response = client.post(f"/projects/{project.id}/entries", json=invalid_data)
    print(response.json())
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
    # Check that source information is still included after update
    assert "source" in data
    assert data["source"] is not None
    assert data["source"]["id"] == str(entry.source.id)
    assert data["source"]["name"] == entry.source.name
    # Check that source_author and author information is still included after update
    assert "source_author" in data
    assert data["source_author"] is not None
    assert data["source_author"]["id"] == str(entry.source_author.id)
    assert (
        data["source_author"]["source_author_id"]
        == entry.source_author.source_author_id
    )
    # Check that author information is still included within source_author after update
    assert "author" in data["source_author"]
    assert data["source_author"]["author"] is not None
    assert data["source_author"]["author"]["id"] == str(entry.source_author.author.id)
    assert (
        data["source_author"]["author"]["display_name"]
        == entry.source_author.author.display_name
    )


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
    """Test POST /projects/{project_id}/entries/search with exact match."""
    entry = setup_entry

    search_filters = {"title": entry.title}

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    assert data["data"][0]["id"] == str(entry.id)
    # Check that source information is included in search results
    assert "source" in data["data"][0]
    assert data["data"][0]["source"] is not None
    assert data["data"][0]["source"]["id"] == str(entry.source.id)
    assert data["data"][0]["source"]["name"] == entry.source.name
    # Check that source_author and author information is included in search results
    assert "source_author" in data["data"][0]
    assert data["data"][0]["source_author"] is not None
    assert data["data"][0]["source_author"]["id"] == str(entry.source_author.id)
    assert (
        data["data"][0]["source_author"]["source_author_id"]
        == entry.source_author.source_author_id
    )
    # Check that author information is included within source_author in search results
    assert "author" in data["data"][0]["source_author"]
    assert data["data"][0]["source_author"]["author"] is not None
    assert data["data"][0]["source_author"]["author"]["id"] == str(
        entry.source_author.author.id
    )
    assert (
        data["data"][0]["source_author"]["author"]["display_name"]
        == entry.source_author.author.display_name
    )


def test_search_entries_partial_match(client, setup_entry):
    """Test POST /projects/{project_id}/entries/search with partial match using ilike."""
    entry = setup_entry
    partial_title = entry.title[: max(1, len(entry.title) // 2)]

    search_filters = {"title": {"operator": "ilike", "value": f"%{partial_title}%"}}

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1


def test_search_entries_by_author(client, setup_entry):
    """Test POST /projects/{project_id}/entries/search by author_id."""
    entry = setup_entry

    search_filters = {"source_author_id": str(entry.source_author_id)}

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1


def test_search_entries_by_project(client, setup_entry):
    """Test POST /projects/{project_id}/entries/search by project_id."""
    entry = setup_entry

    search_filters = {"project_id": str(entry.project_id)}

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1


def test_search_entries_no_results(client, setup_project):
    """Test POST /projects/{project_id}/entries/search with filters that return no results."""
    project = setup_project
    search_filters = {"external_id": str(uuid4())}

    response = client.post(
        f"/projects/{project.id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 0


def test_list_entries_pagination(client, setup_entry):
    """Test GET /projects/{project_id}/entries with pagination parameters."""
    entry = setup_entry

    # Test with skip and limit
    response = client.get(f"/projects/{entry.project_id}/entries?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 1

    # Test with different pagination
    response = client.get(f"/projects/{entry.project_id}/entries?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


def test_list_entries_invalid_project(client):
    """Test GET /projects/{project_id}/entries with non-existent project."""
    fake_project_id = uuid4()
    response = client.get(f"/projects/{fake_project_id}/entries")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_entry_invalid_project(client, setup_source, setup_source_author):
    """Test POST /projects/{project_id}/entries with non-existent project."""
    fake_project_id = uuid4()
    source = setup_source
    source_author = setup_source_author

    entry_data = {
        "title": "Test Entry",
        "body": "This is a test entry body",
        "source_id": str(source.id),
        "external_id": str(uuid4()),
        "tags": ["test", "example"],
        "labels": {"priority": "high"},
        "meta_data": {"created_by": "test"},
        "source_author_id": str(source_author.id),
    }

    response = client.post(f"/projects/{fake_project_id}/entries", json=entry_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_search_entries_invalid_project(client):
    """Test POST /projects/{project_id}/entries/search with non-existent project."""
    fake_project_id = uuid4()
    search_filters = {"title": "test"}

    response = client.post(
        f"/projects/{fake_project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
