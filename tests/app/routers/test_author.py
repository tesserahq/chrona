from uuid import uuid4


def test_list_authors(client, setup_author):
    """Test GET /workspaces/{workspace_id}/authors endpoint."""
    author = setup_author
    workspace_id = author.workspace_id

    response = client.get(f"/workspaces/{workspace_id}/authors")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our author in the response
    author_found = False
    for item in data["items"]:
        if item["id"] == str(author.id):
            author_found = True
            assert item["display_name"] == author.display_name
            assert item["email"] == author.email
            assert item["avatar_url"] == author.avatar_url
            assert item["workspace_id"] == str(author.workspace_id)
            break
    assert author_found


def test_list_authors_workspace_not_found(client):
    """Test GET /workspaces/{workspace_id}/authors with non-existent workspace."""
    fake_workspace_id = uuid4()
    response = client.get(f"/workspaces/{fake_workspace_id}/authors")
    assert response.status_code == 404


def test_get_author(client, setup_author):
    """Test GET /authors/{author_id} endpoint."""
    author = setup_author

    response = client.get(f"/authors/{author.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(author.id)
    assert data["display_name"] == author.display_name
    assert data["email"] == author.email
    assert data["avatar_url"] == author.avatar_url
    assert data["workspace_id"] == str(author.workspace_id)


def test_get_author_not_found(client):
    """Test GET /authors/{author_id} with non-existent author."""
    fake_author_id = uuid4()
    response = client.get(f"/authors/{fake_author_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Author not found"


def test_create_author(client, setup_workspace):
    """Test POST /workspaces/{workspace_id}/authors endpoint."""
    workspace = setup_workspace

    author_data = {
        "display_name": "Test Author",
        "email": "test@example.com",
        "avatar_url": "https://example.com/avatar.jpg",
        "tags": ["test", "example"],
        "labels": {"type": "user"},
        "meta_data": {"source": "test"},
    }

    response = client.post(f"/workspaces/{workspace.id}/authors", json=author_data)
    assert response.status_code == 201
    data = response.json()
    assert data["display_name"] == author_data["display_name"]
    assert data["email"] == author_data["email"]
    assert data["avatar_url"] == author_data["avatar_url"]
    assert data["workspace_id"] == str(workspace.id)
    assert "test" in data["tags"]
    assert data["labels"]["type"] == "user"


def test_create_author_invalid_data(client, setup_workspace):
    """Test POST /workspaces/{workspace_id}/authors with invalid data."""
    workspace = setup_workspace

    invalid_data = {
        "display_name": "",  # Empty display_name should fail validation
        "email": "invalid-email",  # Invalid email format
    }

    response = client.post(f"/workspaces/{workspace.id}/authors", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_create_author_workspace_not_found(client):
    """Test POST /workspaces/{workspace_id}/authors with non-existent workspace."""
    fake_workspace_id = uuid4()
    author_data = {
        "display_name": "Test Author",
        "email": "test@example.com",
        "avatar_url": "https://example.com/avatar.jpg",
    }

    response = client.post(f"/workspaces/{fake_workspace_id}/authors", json=author_data)
    assert response.status_code == 404


def test_update_author(client, setup_author):
    """Test PUT /authors/{author_id} endpoint."""
    author = setup_author

    update_data = {
        "display_name": "Updated Author Name",
        "email": "updated@example.com",
        "tags": ["updated", "modified"],
    }

    response = client.put(f"/authors/{author.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(author.id)
    assert data["display_name"] == update_data["display_name"]
    assert data["email"] == update_data["email"]
    assert "updated" in data["tags"]


def test_update_author_not_found(client):
    """Test PUT /authors/{author_id} with non-existent author."""
    fake_author_id = uuid4()
    update_data = {"display_name": "Updated Name"}

    response = client.put(f"/authors/{fake_author_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Author not found"


def test_delete_author(client, setup_author):
    """Test DELETE /authors/{author_id} endpoint."""
    author = setup_author

    response = client.delete(f"/authors/{author.id}")
    assert response.status_code == 204

    # Verify author is soft deleted (not found)
    get_response = client.get(f"/authors/{author.id}")
    assert get_response.status_code == 404


def test_delete_author_not_found(client):
    """Test DELETE /authors/{author_id} with non-existent author."""
    fake_author_id = uuid4()
    response = client.delete(f"/authors/{fake_author_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Author not found"


def test_list_authors_pagination(client, setup_author):
    """Test GET /workspaces/{workspace_id}/authors with pagination parameters."""
    author = setup_author
    workspace_id = author.workspace_id

    # Test with page and size (fastapi-pagination format)
    response = client.get(f"/workspaces/{workspace_id}/authors?page=1&size=1")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 1
    assert "page" in data
    assert "size" in data
    assert "total" in data
    assert "pages" in data

    # Test with different pagination
    response = client.get(f"/workspaces/{workspace_id}/authors?page=2&size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "page" in data
    assert "size" in data
    assert "total" in data
    assert "pages" in data


def test_create_author_with_user_id(client, setup_workspace, setup_user):
    """Test POST /workspaces/{workspace_id}/authors with user_id."""
    workspace = setup_workspace
    user = setup_user

    author_data = {
        "display_name": "Test Author with User",
        "email": "test@example.com",
        "avatar_url": "https://example.com/avatar.jpg",
        "user_id": str(user.id),
    }

    response = client.post(f"/workspaces/{workspace.id}/authors", json=author_data)
    assert response.status_code == 201
    data = response.json()
    assert data["display_name"] == author_data["display_name"]
    assert data["user_id"] == str(user.id)
    assert data["workspace_id"] == str(workspace.id)


def test_update_author_partial(client, setup_author):
    """Test PUT /authors/{author_id} with partial update."""
    author = setup_author

    # Only update display_name, leave other fields unchanged
    update_data = {"display_name": "Partially Updated Name"}

    response = client.put(f"/authors/{author.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(author.id)
    assert data["display_name"] == update_data["display_name"]
    # Other fields should remain unchanged
    assert data["email"] == author.email
    assert data["avatar_url"] == author.avatar_url


def test_merge_authors_validation_error(client, setup_workspace):
    """Test POST /workspaces/{workspace_id}/authors/merge with validation errors."""
    workspace = setup_workspace

    # Test empty author_ids list
    payload = {"author_ids": [], "merge_to_author_id": str(uuid4())}

    response = client.post(f"/workspaces/{workspace.id}/authors/merge", json=payload)
    assert response.status_code == 422  # Validation error due to min_length=1

    # Test invalid UUID format
    payload = {
        "author_ids": ["invalid-uuid"],
        "merge_to_author_id": "also-invalid-uuid",
    }

    response = client.post(f"/workspaces/{workspace.id}/authors/merge", json=payload)
    assert response.status_code == 422  # Validation error


def test_merge_authors_not_found(client, setup_workspace):
    """Test POST /workspaces/{workspace_id}/authors/merge with non-existent authors."""
    workspace = setup_workspace
    fake_author_id = str(uuid4())
    target_author_id = str(uuid4())

    payload = {"author_ids": [fake_author_id], "merge_to_author_id": target_author_id}

    response = client.post(f"/workspaces/{workspace.id}/authors/merge", json=payload)
    assert response.status_code == 400
    assert "not found in this workspace" in response.json()["detail"]


def test_merge_authors_workspace_not_found(client):
    """Test POST /workspaces/{workspace_id}/authors/merge with non-existent workspace."""
    fake_workspace_id = str(uuid4())
    payload = {"author_ids": [str(uuid4())], "merge_to_author_id": str(uuid4())}

    response = client.post(
        f"/workspaces/{fake_workspace_id}/authors/merge", json=payload
    )
    assert response.status_code == 404
    assert "Workspace not found" in response.json()["detail"]
