from uuid import uuid4


def test_get_digest(client, setup_digest):
    """Test GET /digests/{digest_id} endpoint."""
    digest = setup_digest
    response = client.get(f"/digests/{digest.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(digest.id)
    assert data["title"] == digest.title
    assert data["body"] == digest.body
    assert data["project_id"] == str(digest.project_id)
    assert data["digest_generation_config_id"] == str(
        digest.digest_generation_config_id
    )
    assert data["status"] == digest.status
    assert data["tags"] == digest.tags
    assert data["labels"] == digest.labels
    assert len(data["entries_ids"]) == len(digest.entries_ids)
    assert len(data["entry_updates_ids"]) == len(digest.entry_updates_ids)
    assert "created_at" in data
    assert "updated_at" in data


def test_get_digest_not_found(client):
    """Test GET /digests/{digest_id} endpoint with non-existent digest."""
    non_existent_id = uuid4()
    response = client.get(f"/digests/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest not found"


def test_update_digest(client, setup_digest, faker):
    """Test PUT /digests/{digest_id} endpoint."""
    digest = setup_digest

    update_data = {
        "title": faker.sentence(nb_words=5),
        "body": faker.text(300),
        "tags": ["updated", "test"],
        "labels": {"priority": "low", "updated": "true"},
        "status": "published",
    }

    response = client.put(f"/digests/{digest.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(digest.id)
    assert data["title"] == update_data["title"]
    assert data["body"] == update_data["body"]
    assert data["tags"] == update_data["tags"]
    assert data["labels"] == update_data["labels"]
    assert data["status"] == update_data["status"]
    # Ensure unchanged fields remain the same
    assert data["project_id"] == str(digest.project_id)
    assert data["digest_generation_config_id"] == str(
        digest.digest_generation_config_id
    )


def test_update_digest_partial(client, setup_digest, faker):
    """Test PUT /digests/{digest_id} endpoint with partial update."""
    digest = setup_digest
    original_body = digest.body
    original_tags = digest.tags

    # Only update title
    update_data = {"title": faker.sentence(nb_words=3)}

    response = client.put(f"/digests/{digest.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(digest.id)
    assert data["title"] == update_data["title"]
    # Ensure other fields remain unchanged
    assert data["body"] == original_body
    assert data["tags"] == original_tags
    assert data["project_id"] == str(digest.project_id)


def test_update_digest_not_found(client, faker):
    """Test PUT /digests/{digest_id} endpoint with non-existent digest."""
    non_existent_id = uuid4()

    update_data = {"title": faker.sentence(nb_words=3)}

    response = client.put(f"/digests/{non_existent_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest not found"


def test_update_digest_with_entries_and_updates(client, setup_digest):
    """Test PUT /digests/{digest_id} endpoint updating entries and entry_updates."""
    digest = setup_digest

    new_entry_ids = [uuid4(), uuid4(), uuid4()]
    new_entry_update_ids = [uuid4(), uuid4()]

    update_data = {
        "entries_ids": [str(id) for id in new_entry_ids],  # Convert UUIDs to strings
        "entry_updates_ids": [
            str(id) for id in new_entry_update_ids
        ],  # Convert UUIDs to strings
    }

    response = client.put(f"/digests/{digest.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["entries_ids"]) == 3
    assert len(data["entry_updates_ids"]) == 2
    assert all(str(entry_id) in data["entries_ids"] for entry_id in new_entry_ids)
    assert all(
        str(update_id) in data["entry_updates_ids"]
        for update_id in new_entry_update_ids
    )


def test_delete_digest(client, setup_digest):
    """Test DELETE /digests/{digest_id} endpoint."""
    digest = setup_digest

    response = client.delete(f"/digests/{digest.id}")
    assert response.status_code == 204

    # Verify the digest is no longer accessible
    get_response = client.get(f"/digests/{digest.id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Digest not found"


def test_delete_digest_not_found(client):
    """Test DELETE /digests/{digest_id} endpoint with non-existent digest."""
    non_existent_id = uuid4()

    response = client.delete(f"/digests/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest not found"


def test_digest_router_registered(client):
    """Test that the digest router is properly registered."""
    # Try to access a non-existent digest to verify the router is registered
    # This should return 404 from our router, not a 404 from FastAPI saying route doesn't exist
    response = client.get("/digests/00000000-0000-0000-0000-000000000000")

    # Should get our custom 404 message, not FastAPI's "Not Found"
    assert response.status_code == 404
    assert response.json()["detail"] == "Digest not found"


def test_update_digest_dates(client, setup_digest):
    """Test updating digest dates."""
    digest = setup_digest

    from datetime import datetime, timezone

    new_from_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    new_to_date = datetime(2023, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

    update_data = {
        "from_date": new_from_date.isoformat(),
        "to_date": new_to_date.isoformat(),
    }

    response = client.put(f"/digests/{digest.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    # Parse the returned dates and compare (accounting for potential formatting differences)
    returned_from_date = datetime.fromisoformat(
        data["from_date"].replace("Z", "+00:00")
    )
    returned_to_date = datetime.fromisoformat(data["to_date"].replace("Z", "+00:00"))

    # Make both timezone-aware for comparison
    if returned_from_date.tzinfo is None:
        returned_from_date = returned_from_date.replace(tzinfo=timezone.utc)
    if returned_to_date.tzinfo is None:
        returned_to_date = returned_to_date.replace(tzinfo=timezone.utc)

    assert returned_from_date.replace(microsecond=0) == new_from_date.replace(
        microsecond=0
    )
    assert returned_to_date.replace(microsecond=0) == new_to_date.replace(microsecond=0)


# Note: Authentication tests are handled by the auth middleware and tested separately
# The digest endpoints use the get_current_user dependency which ensures authentication
