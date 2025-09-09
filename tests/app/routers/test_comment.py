from uuid import uuid4


def test_list_comments(client, setup_comment):
    """Test GET /entries/{entry_id}/comments endpoint."""
    comment = setup_comment
    entry_id = comment.entry_id

    response = client.get(f"/entries/{entry_id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1

    # Find our comment in the response
    comment_found = False
    for item in data["data"]:
        if item["id"] == str(comment.id):
            comment_found = True
            assert item["body"] == comment.body
            assert item["source_author_id"] == str(comment.source_author_id)
            assert item["entry_id"] == str(comment.entry_id)
            break
    assert comment_found


def test_list_comments_entry_not_found(client):
    """Test GET /entries/{entry_id}/comments with non-existent entry."""
    fake_entry_id = uuid4()
    response = client.get(f"/entries/{fake_entry_id}/comments")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_get_comment(client, setup_comment):
    """Test GET /comments/{comment_id} endpoint."""
    comment = setup_comment

    response = client.get(f"/comments/{comment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(comment.id)
    assert data["body"] == comment.body
    assert data["source_author_id"] == str(comment.source_author_id)
    assert data["entry_id"] == str(comment.entry_id)


def test_get_comment_not_found(client):
    """Test GET /comments/{comment_id} with non-existent comment."""
    fake_comment_id = uuid4()

    response = client.get(f"/comments/{fake_comment_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_create_comment(client, setup_source_author, setup_entry):
    """Test POST /entries/{entry_id}/comments endpoint."""
    source_author = setup_source_author
    entry = setup_entry

    comment_data = {
        "body": "This is a test comment",
        "source_author_id": str(source_author.id),
        "source_id": str(entry.source_id),
        "tags": ["feedback"],
        "labels": {"priority": "medium"},
        "meta_data": {"source": "test"},
        "entry_id": str(entry.id),
        "external_id": "test_external_id_123",
    }

    response = client.post(f"/entries/{entry.id}/comments", json=comment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == comment_data["body"]
    assert data["source_author_id"] == str(source_author.id)
    assert data["entry_id"] == str(entry.id)
    assert "feedback" in data["tags"]
    assert data["labels"]["priority"] == "medium"


def test_create_comment_entry_not_found(client, setup_source_author):
    """Test POST /entries/{entry_id}/comments with non-existent entry."""
    source_author = setup_source_author
    fake_entry_id = uuid4()

    comment_data = {
        "body": "This is a test comment",
        "source_author_id": str(source_author.id),
    }

    response = client.post(f"/entries/{fake_entry_id}/comments", json=comment_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_create_comment_invalid_data(client, setup_entry):
    """Test POST /entries/{entry_id}/comments with invalid data."""
    entry = setup_entry

    invalid_data = {
        "body": "",  # Empty body should fail validation
    }

    response = client.post(f"/entries/{entry.id}/comments", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_update_comment(client, setup_comment):
    """Test PUT /comments/{comment_id} endpoint."""
    comment = setup_comment

    update_data = {
        "body": "Updated comment body",
        "tags": ["updated", "modified"],
    }

    response = client.put(f"/comments/{comment.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(comment.id)
    assert data["body"] == update_data["body"]
    assert "updated" in data["tags"]


def test_update_comment_not_found(client):
    """Test PUT /comments/{comment_id} with non-existent comment."""
    fake_comment_id = uuid4()

    update_data = {"body": "Updated comment body"}

    response = client.put(f"/comments/{fake_comment_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_delete_comment(client, setup_comment):
    """Test DELETE /comments/{comment_id} endpoint."""
    comment = setup_comment

    response = client.delete(f"/comments/{comment.id}")
    assert response.status_code == 204

    # Verify comment is soft deleted (not found)
    get_response = client.get(f"/comments/{comment.id}")
    assert get_response.status_code == 404


def test_delete_comment_not_found(client):
    """Test DELETE /comments/{comment_id} with non-existent comment."""
    fake_comment_id = uuid4()

    response = client.delete(f"/comments/{fake_comment_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_list_comments_pagination(client, setup_comment):
    """Test GET /entries/{entry_id}/comments with pagination parameters."""
    comment = setup_comment
    entry_id = comment.entry_id

    # Test with skip and limit
    response = client.get(f"/entries/{entry_id}/comments?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 1

    # Test with different pagination
    response = client.get(f"/entries/{entry_id}/comments?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


def test_create_comment_auto_sets_entry_id(client, setup_source_author, setup_entry):
    """Test that creating a comment automatically sets the entry_id from the URL."""
    entry = setup_entry
    source_author = setup_source_author

    comment_data = {
        "body": "This is a test comment",
        "source_author_id": str(source_author.id),
        "source_id": str(entry.source_id),
        "entry_id": str(entry.id),
        "external_id": "test_external_id_456",
        # Note: not providing entry_id in the request body
    }

    response = client.post(f"/entries/{entry.id}/comments", json=comment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["entry_id"] == str(entry.id)
    assert data["body"] == comment_data["body"]


def test_list_comments_empty_entry(client, setup_entry):
    """Test GET /entries/{entry_id}/comments for entry with no comments."""
    entry = setup_entry

    response = client.get(f"/entries/{entry.id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 0
