from uuid import uuid4


def test_list_gazettes(client, setup_gazette, setup_gazette_minimal):
    """Test GET /projects/{project_id}/gazettes endpoint."""
    gazette1 = setup_gazette
    gazette2 = setup_gazette_minimal
    project_id = gazette1.project_id

    response = client.get(f"/projects/{project_id}/gazettes")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data

    # Should have at least 2 gazettes
    assert data["total"] >= 2
    gazette_ids = [item["id"] for item in data["items"]]
    assert str(gazette1.id) in gazette_ids
    assert str(gazette2.id) in gazette_ids


def test_list_gazettes_nonexistent_project(client):
    """Test GET /projects/{project_id}/gazettes with non-existent project."""
    non_existent_id = uuid4()
    response = client.get(f"/projects/{non_existent_id}/gazettes")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_gazette(client, setup_project):
    """Test POST /projects/{project_id}/gazettes endpoint."""
    project = setup_project
    gazette_data = {
        "name": "Test Gazette Name",
        "header": "Test Gazette Header",
        "subheader": "Test Subheader",
        "theme": "technology",
        "tags": ["tech", "news"],
        "labels": {"category": "weekly", "priority": 1},
        "project_id": str(project.id),  # This should be overridden by URL
        "share_key": "test-share-123",
    }

    response = client.post(f"/projects/{project.id}/gazettes", json=gazette_data)
    assert response.status_code == 201

    created_gazette = response.json()
    assert created_gazette["name"] == gazette_data["name"]
    assert created_gazette["header"] == gazette_data["header"]
    assert created_gazette["subheader"] == gazette_data["subheader"]
    assert created_gazette["theme"] == gazette_data["theme"]
    assert created_gazette["tags"] == gazette_data["tags"]
    assert created_gazette["labels"] == gazette_data["labels"]
    assert created_gazette["project_id"] == str(project.id)
    # share_key should NOT be in regular response
    assert "share_key" not in created_gazette
    assert "id" in created_gazette
    assert "created_at" in created_gazette
    assert "updated_at" in created_gazette


def test_create_gazette_minimal(client, setup_project):
    """Test POST /projects/{project_id}/gazettes with minimal data."""
    project = setup_project
    gazette_data = {
        "name": "Minimal Gazette Name",
        "header": "Minimal Gazette",
        "project_id": str(project.id),
    }

    response = client.post(f"/projects/{project.id}/gazettes", json=gazette_data)
    assert response.status_code == 201

    created_gazette = response.json()
    assert created_gazette["name"] == gazette_data["name"]
    assert created_gazette["header"] == gazette_data["header"]
    assert created_gazette["subheader"] is None
    assert created_gazette["theme"] is None
    assert created_gazette["tags"] == []
    assert created_gazette["labels"] == {}
    assert created_gazette["project_id"] == str(project.id)
    # share_key should NOT be in regular response
    assert "share_key" not in created_gazette


def test_create_gazette_nonexistent_project(client):
    """Test POST /projects/{project_id}/gazettes with non-existent project."""
    non_existent_id = uuid4()
    gazette_data = {
        "name": "Test Gazette Name",
        "header": "Test Gazette",
        "project_id": str(non_existent_id),
    }

    response = client.post(f"/projects/{non_existent_id}/gazettes", json=gazette_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_get_gazette(client, setup_gazette):
    """Test GET /gazettes/{gazette_id} endpoint."""
    gazette = setup_gazette

    response = client.get(f"/gazettes/{gazette.id}")
    assert response.status_code == 200

    retrieved_gazette = response.json()
    assert retrieved_gazette["id"] == str(gazette.id)
    assert retrieved_gazette["name"] == gazette.name
    assert retrieved_gazette["header"] == gazette.header
    assert retrieved_gazette["subheader"] == gazette.subheader
    assert retrieved_gazette["theme"] == gazette.theme
    assert retrieved_gazette["tags"] == gazette.tags
    assert retrieved_gazette["labels"] == gazette.labels
    assert retrieved_gazette["project_id"] == str(gazette.project_id)
    # share_key should NOT be in regular response
    assert "share_key" not in retrieved_gazette


def test_get_gazette_nonexistent(client):
    """Test GET /gazettes/{gazette_id} with non-existent gazette."""
    non_existent_id = uuid4()
    response = client.get(f"/gazettes/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Gazette not found"


def test_update_gazette(client, setup_gazette):
    """Test PUT /gazettes/{gazette_id} endpoint."""
    gazette = setup_gazette
    update_data = {
        "name": "Updated Name",
        "header": "Updated Header",
        "subheader": "Updated Subheader",
        "theme": "updated_theme",
        "tags": ["updated", "tags"],
        "labels": {"updated": "labels"},
    }

    response = client.put(f"/gazettes/{gazette.id}", json=update_data)
    assert response.status_code == 200

    updated_gazette = response.json()
    assert updated_gazette["id"] == str(gazette.id)
    assert updated_gazette["name"] == update_data["name"]
    assert updated_gazette["header"] == update_data["header"]
    assert updated_gazette["subheader"] == update_data["subheader"]
    assert updated_gazette["theme"] == update_data["theme"]
    assert updated_gazette["tags"] == update_data["tags"]
    assert updated_gazette["labels"] == update_data["labels"]
    # Project ID should remain unchanged
    assert updated_gazette["project_id"] == str(gazette.project_id)


def test_update_gazette_partial(client, setup_gazette):
    """Test PUT /gazettes/{gazette_id} with partial update."""
    gazette = setup_gazette
    original_subheader = gazette.subheader

    update_data = {
        "header": "Partially Updated Header",
    }

    response = client.put(f"/gazettes/{gazette.id}", json=update_data)
    assert response.status_code == 200

    updated_gazette = response.json()
    assert updated_gazette["header"] == update_data["header"]
    # Unchanged fields should remain the same
    assert updated_gazette["subheader"] == original_subheader
    assert updated_gazette["project_id"] == str(gazette.project_id)


def test_update_gazette_nonexistent(client):
    """Test PUT /gazettes/{gazette_id} with non-existent gazette."""
    non_existent_id = uuid4()
    update_data = {
        "header": "Updated Header",
    }

    response = client.put(f"/gazettes/{non_existent_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Gazette not found"


def test_delete_gazette(client, setup_gazette):
    """Test DELETE /gazettes/{gazette_id} endpoint."""
    gazette = setup_gazette

    response = client.delete(f"/gazettes/{gazette.id}")
    assert response.status_code == 204

    # Verify the gazette is deleted (soft delete)
    response = client.get(f"/gazettes/{gazette.id}")
    assert response.status_code == 404


def test_delete_gazette_nonexistent(client):
    """Test DELETE /gazettes/{gazette_id} with non-existent gazette."""
    non_existent_id = uuid4()
    response = client.delete(f"/gazettes/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Gazette not found"


def test_get_gazette_by_share_key(client, setup_gazette_with_share_key):
    """Test GET /gazettes/share/{share_key} endpoint."""
    gazette = setup_gazette_with_share_key

    response = client.get(f"/gazettes/share/{gazette.share_key}")
    assert response.status_code == 200

    response_data = response.json()
    # Response should now contain gazette and digests
    assert "gazette" in response_data
    assert "digests" in response_data

    retrieved_gazette = response_data["gazette"]
    assert retrieved_gazette["id"] == str(gazette.id)
    assert retrieved_gazette["header"] == gazette.header
    # share_key should NOT be in regular response (even when accessed via share key)
    assert "share_key" not in retrieved_gazette

    # Digests should be a list (empty or with matching digests)
    digests = response_data["digests"]
    assert isinstance(digests, list)


def test_get_gazette_by_share_key_nonexistent(client):
    """Test GET /gazettes/share/{share_key} with non-existent share key."""
    non_existent_key = "non-existent-key"
    response = client.get(f"/gazettes/share/{non_existent_key}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Gazette not found"


def test_list_gazettes_pagination(client, setup_project):
    """Test pagination for GET /projects/{project_id}/gazettes."""
    project = setup_project

    # Create multiple gazettes using the API
    for i in range(5):
        gazette_data = {
            "name": f"Test Gazette {i}",
            "header": f"Test Gazette {i}",
            "project_id": str(project.id),
        }
        response = client.post(f"/projects/{project.id}/gazettes", json=gazette_data)
        assert response.status_code == 201

    # Test first page
    response = client.get(f"/projects/{project.id}/gazettes?page=1&size=2")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["total"] >= 5

    # Test second page
    response = client.get(f"/projects/{project.id}/gazettes?page=2&size=2")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 2
    assert data["size"] == 2


def test_create_gazette_project_id_override(client, setup_project):
    """Test that project_id in request body is overridden by URL parameter."""
    project = setup_project
    wrong_project_id = uuid4()

    gazette_data = {
        "name": "Test Override",
        "header": "Test Override",
        "project_id": str(wrong_project_id),  # This should be ignored
    }

    response = client.post(f"/projects/{project.id}/gazettes", json=gazette_data)
    assert response.status_code == 201

    created_gazette = response.json()
    # Should use project ID from URL, not request body
    assert created_gazette["project_id"] == str(project.id)
    assert created_gazette["project_id"] != str(wrong_project_id)


def test_generate_gazette_share_key_new(client, setup_gazette_minimal):
    """Test POST /gazettes/{gazette_id}/share endpoint for gazette without share key."""
    gazette = setup_gazette_minimal
    # Ensure gazette doesn't have a share key initially
    assert gazette.share_key is None

    response = client.post(f"/gazettes/{gazette.id}/share")
    assert response.status_code == 200

    share_response = response.json()
    assert share_response["id"] == str(gazette.id)
    assert share_response["header"] == gazette.header
    # share_key SHOULD be in share response
    assert "share_key" in share_response
    assert share_response["share_key"] is not None
    assert len(share_response["share_key"]) > 10  # Should be a reasonable length


def test_generate_gazette_share_key_existing(client, setup_gazette_with_share_key):
    """Test POST /gazettes/{gazette_id}/share endpoint for gazette with existing share key."""
    gazette = setup_gazette_with_share_key
    original_share_key = gazette.share_key

    response = client.post(f"/gazettes/{gazette.id}/share")
    assert response.status_code == 200

    share_response = response.json()
    assert share_response["id"] == str(gazette.id)
    assert share_response["header"] == gazette.header
    # share_key SHOULD be in share response and should be the same
    assert "share_key" in share_response
    assert share_response["share_key"] == original_share_key


def test_generate_gazette_share_key_nonexistent(client):
    """Test POST /gazettes/{gazette_id}/share with non-existent gazette."""
    non_existent_id = uuid4()
    response = client.post(f"/gazettes/{non_existent_id}/share")
    assert response.status_code == 404
    assert response.json()["detail"] == "Gazette not found"


def test_share_key_not_in_regular_responses(client, setup_gazette_with_share_key):
    """Test that share_key is not returned in regular endpoints even if gazette has one."""
    gazette = setup_gazette_with_share_key

    # Test GET endpoint
    response = client.get(f"/gazettes/{gazette.id}")
    assert response.status_code == 200
    assert "share_key" not in response.json()

    # Test UPDATE endpoint
    update_data = {"header": "Updated Header"}
    response = client.put(f"/gazettes/{gazette.id}", json=update_data)
    assert response.status_code == 200
    assert "share_key" not in response.json()

    # Test LIST endpoint
    response = client.get(f"/projects/{gazette.project_id}/gazettes")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "share_key" not in item


def test_share_key_uniqueness(client, setup_project):
    """Test that generated share keys are unique."""
    project = setup_project

    # Create two gazettes
    gazette1_data = {
        "name": "Gazette 1",
        "header": "Gazette 1",
        "project_id": str(project.id),
    }
    gazette2_data = {
        "name": "Gazette 2",
        "header": "Gazette 2",
        "project_id": str(project.id),
    }

    response1 = client.post(f"/projects/{project.id}/gazettes", json=gazette1_data)
    response2 = client.post(f"/projects/{project.id}/gazettes", json=gazette2_data)

    assert response1.status_code == 201
    assert response2.status_code == 201

    gazette1_id = response1.json()["id"]
    gazette2_id = response2.json()["id"]

    # Generate share keys for both
    share1_response = client.post(f"/gazettes/{gazette1_id}/share")
    share2_response = client.post(f"/gazettes/{gazette2_id}/share")

    assert share1_response.status_code == 200
    assert share2_response.status_code == 200

    share_key1 = share1_response.json()["share_key"]
    share_key2 = share2_response.json()["share_key"]

    # Share keys should be different
    assert share_key1 != share_key2
    assert share_key1 is not None
    assert share_key2 is not None


def test_get_gazette_with_digests_basic(client, setup_gazette_with_share_key):
    """Test GET /gazettes/share/{share_key} returns gazette with digests structure."""
    gazette = setup_gazette_with_share_key

    response = client.get(f"/gazettes/share/{gazette.share_key}")
    assert response.status_code == 200

    response_data = response.json()
    # Response should now contain gazette and digests
    assert "gazette" in response_data
    assert "digests" in response_data

    # Gazette should be the same
    retrieved_gazette = response_data["gazette"]
    assert retrieved_gazette["id"] == str(gazette.id)
    assert retrieved_gazette["header"] == gazette.header

    # Digests should be a list (may be empty if no matching digests)
    digests = response_data["digests"]
    assert isinstance(digests, list)


def test_gazette_digest_filtering_service_basic(db, setup_gazette_with_share_key):
    """Test the service method for filtering digests without creating complex test data."""
    from app.services.gazette_service import GazetteService

    service = GazetteService(db)
    gazette = setup_gazette_with_share_key

    # Test the service method (should return empty list if no matching digests)
    filtered_digests = service.get_gazette_digests(gazette)

    # Should return a list (may be empty)
    assert isinstance(filtered_digests, list)


def test_regenerate_gazette_share_key_new(client, setup_gazette_minimal):
    """Test POST /gazettes/{gazette_id}/regenerate-share-key for gazette without share key."""
    gazette = setup_gazette_minimal
    # Ensure gazette doesn't have a share key initially
    assert gazette.share_key is None

    response = client.post(f"/gazettes/{gazette.id}/regenerate-share-key")
    assert response.status_code == 200

    regenerated_response = response.json()
    assert regenerated_response["id"] == str(gazette.id)
    assert regenerated_response["header"] == gazette.header
    # share_key should NOT be in regular response (even after regeneration)
    assert "share_key" not in regenerated_response

    # Verify the share key was actually generated by calling the share endpoint
    share_response = client.post(f"/gazettes/{gazette.id}/share")
    assert share_response.status_code == 200
    assert "share_key" in share_response.json()
    assert share_response.json()["share_key"] is not None


def test_regenerate_gazette_share_key_existing(client, setup_gazette_with_share_key):
    """Test POST /gazettes/{gazette_id}/regenerate-share-key for gazette with existing share key."""
    gazette = setup_gazette_with_share_key
    original_share_key = gazette.share_key

    response = client.post(f"/gazettes/{gazette.id}/regenerate-share-key")
    assert response.status_code == 200

    regenerated_response = response.json()
    assert regenerated_response["id"] == str(gazette.id)
    assert regenerated_response["header"] == gazette.header
    # share_key should NOT be in regular response
    assert "share_key" not in regenerated_response

    # Verify the share key was actually changed by calling the share endpoint
    share_response = client.post(f"/gazettes/{gazette.id}/share")
    assert share_response.status_code == 200
    new_share_key = share_response.json()["share_key"]
    assert new_share_key != original_share_key  # Should be different
    assert new_share_key is not None


def test_regenerate_gazette_share_key_nonexistent(client):
    """Test POST /gazettes/{gazette_id}/regenerate-share-key with non-existent gazette."""
    non_existent_id = uuid4()
    response = client.post(f"/gazettes/{non_existent_id}/regenerate-share-key")
    assert response.status_code == 404
    assert response.json()["detail"] == "Gazette not found"


def test_regenerate_share_key_invalidates_old_key(client, setup_gazette_with_share_key):
    """Test that regenerating share key invalidates the old one."""
    gazette = setup_gazette_with_share_key
    original_share_key = gazette.share_key

    # Verify original share key works
    response = client.get(f"/gazettes/share/{original_share_key}")
    assert response.status_code == 200
    assert response.json()["gazette"]["id"] == str(gazette.id)

    # Regenerate share key
    response = client.post(f"/gazettes/{gazette.id}/regenerate-share-key")
    assert response.status_code == 200

    # Get the new share key
    share_response = client.post(f"/gazettes/{gazette.id}/share")
    new_share_key = share_response.json()["share_key"]

    # Verify old share key no longer works
    response = client.get(f"/gazettes/share/{original_share_key}")
    assert response.status_code == 404  # Old key should not work

    # Verify new share key works
    response = client.get(f"/gazettes/share/{new_share_key}")
    assert response.status_code == 200
    assert response.json()["gazette"]["id"] == str(gazette.id)
