from uuid import uuid4


def test_list_entries(client, setup_entry):
    """Test GET /projects/{project_id}/entries endpoint."""
    entry = setup_entry

    response = client.get(f"/projects/{entry.project_id}/entries")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Find our entry in the response
    entry_found = False
    for item in data["items"]:
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
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["id"] == str(entry.id)
    # Check that source information is included in search results
    assert "source" in data["items"][0]
    assert data["items"][0]["source"] is not None
    assert data["items"][0]["source"]["id"] == str(entry.source.id)
    assert data["items"][0]["source"]["name"] == entry.source.name
    # Check that source_author and author information is included in search results
    assert "source_author" in data["items"][0]
    assert data["items"][0]["source_author"] is not None
    assert data["items"][0]["source_author"]["id"] == str(entry.source_author.id)
    assert (
        data["items"][0]["source_author"]["source_author_id"]
        == entry.source_author.source_author_id
    )
    # Check that author information is included within source_author in search results
    assert "author" in data["items"][0]["source_author"]
    assert data["items"][0]["source_author"]["author"] is not None
    assert data["items"][0]["source_author"]["author"]["id"] == str(
        entry.source_author.author.id
    )
    assert (
        data["items"][0]["source_author"]["author"]["display_name"]
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
    assert "items" in data
    assert len(data["items"]) >= 1


def test_search_entries_by_author(client, setup_entry):
    """Test POST /projects/{project_id}/entries/search by author_id."""
    entry = setup_entry

    search_filters = {"source_author_id": str(entry.source_author_id)}

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_search_entries_by_project(client, setup_entry):
    """Test POST /projects/{project_id}/entries/search by project_id."""
    entry = setup_entry

    search_filters = {"project_id": str(entry.project_id)}

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_search_entries_no_results(client, setup_project):
    """Test POST /projects/{project_id}/entries/search with filters that return no results."""
    project = setup_project
    search_filters = {"external_id": str(uuid4())}

    response = client.post(
        f"/projects/{project.id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 0


def test_list_entries_pagination(client, setup_entry):
    """Test GET /projects/{project_id}/entries with pagination parameters."""
    entry = setup_entry

    # Test with page and size (fastapi-pagination format)
    response = client.get(f"/projects/{entry.project_id}/entries?page=1&size=1")
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
    response = client.get(f"/projects/{entry.project_id}/entries?page=2&size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "page" in data
    assert "size" in data
    assert "total" in data
    assert "pages" in data


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


def test_search_entries_by_source_created_at_date_range(client, setup_entry, db):
    """Test POST /projects/{project_id}/entries/search with source_created_at date range filter."""
    entry = setup_entry
    from datetime import datetime, timedelta, timezone

    # Set a specific source_created_at date for the entry
    entry_source_created_at = datetime(2025, 11, 2, 12, 0, 0, tzinfo=timezone.utc)
    entry.source_created_at = entry_source_created_at
    db.commit()
    db.refresh(entry)

    # Search for entries created in a range that includes our entry
    from_date = (
        (entry_source_created_at - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )
    to_date = (
        (entry_source_created_at + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )

    search_filters = {
        "source_created_at": {"from": from_date, "to": to_date},
    }

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(item["id"] == str(entry.id) for item in data["items"])

    # Search for entries created before our entry (should exclude it)
    before_from = (
        (entry_source_created_at - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    )
    before_to = (
        (entry_source_created_at - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )

    search_filters = {
        "source_created_at": {"from": before_from, "to": before_to},
    }

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Our entry should not be in the results
    assert not any(item["id"] == str(entry.id) for item in data["items"])


def test_search_entries_by_source_updated_at_date_range(client, setup_entry, db):
    """Test POST /projects/{project_id}/entries/search with source_updated_at date range filter."""
    entry = setup_entry
    from datetime import datetime, timedelta, timezone

    # Set a specific source_updated_at date for the entry
    entry_source_updated_at = datetime(2025, 11, 2, 12, 0, 0, tzinfo=timezone.utc)
    entry.source_updated_at = entry_source_updated_at
    db.commit()
    db.refresh(entry)

    # Search for entries updated in a range that includes our entry
    from_date = (
        (entry_source_updated_at - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )
    to_date = (
        (entry_source_updated_at + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )

    search_filters = {
        "source_updated_at": {"from": from_date, "to": to_date},
    }

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(item["id"] == str(entry.id) for item in data["items"])

    # Search for entries updated before our entry was updated (should exclude it)
    before_from = (
        (entry_source_updated_at - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    )
    before_to = (
        (entry_source_updated_at - timedelta(hours=1))
        .isoformat()
        .replace("+00:00", "Z")
    )

    search_filters = {
        "source_updated_at": {"from": before_from, "to": before_to},
    }

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Our entry should not be in the results since it was updated more recently
    assert not any(item["id"] == str(entry.id) for item in data["items"])


def test_search_entries_combined_date_range_filters(client, setup_entry, db):
    """Test POST /projects/{project_id}/entries/search with both source_created_at and source_updated_at filters."""
    entry = setup_entry
    from datetime import datetime, timedelta, timezone

    # Set specific source_created_at and source_updated_at dates for the entry
    entry_source_created_at = datetime(2025, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    entry_source_updated_at = datetime(2025, 11, 2, 12, 0, 0, tzinfo=timezone.utc)
    entry.source_created_at = entry_source_created_at
    entry.source_updated_at = entry_source_updated_at
    db.commit()
    db.refresh(entry)

    # Search with both filters
    created_from = (
        (entry_source_created_at - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )
    created_to = (
        (entry_source_created_at + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )
    updated_from = (
        (entry_source_updated_at - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )
    updated_to = (
        (entry_source_updated_at + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    )

    search_filters = {
        "source_created_at": {"from": created_from, "to": created_to},
        "source_updated_at": {"from": updated_from, "to": updated_to},
    }

    response = client.post(
        f"/projects/{entry.project_id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(item["id"] == str(entry.id) for item in data["items"])


def test_search_entries_by_source_created_at_date_range_comprehensive(
    client, setup_project, setup_source, setup_source_author, db
):
    """Test source_created_at date range filtering with entries created at specific dates."""
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.models.entry import Entry

    project = setup_project
    source = setup_source
    source_author = setup_source_author

    # Create entries with specific source_created_at dates
    # Entry 1: Inside the range (2025-11-01)
    entry1_date = datetime(2025, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    entry1 = Entry(
        title="Entry 1 - Inside Range",
        body="Test body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test"],
        source_author_id=source_author.id,
        project_id=project.id,
        source_created_at=entry1_date,
    )
    db.add(entry1)
    db.commit()
    db.refresh(entry1)

    # Entry 2: Inside the range (2025-11-02)
    entry2_date = datetime(2025, 11, 2, 12, 0, 0, tzinfo=timezone.utc)
    entry2 = Entry(
        title="Entry 2 - Inside Range",
        body="Test body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test"],
        source_author_id=source_author.id,
        project_id=project.id,
        source_created_at=entry2_date,
    )
    db.add(entry2)
    db.commit()
    db.refresh(entry2)

    # Entry 3: Before the range (2025-10-29)
    entry3_date = datetime(2025, 10, 29, 12, 0, 0, tzinfo=timezone.utc)
    entry3 = Entry(
        title="Entry 3 - Before Range",
        body="Test body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test"],
        source_author_id=source_author.id,
        project_id=project.id,
        source_created_at=entry3_date,
    )
    db.add(entry3)
    db.commit()
    db.refresh(entry3)

    # Entry 4: After the range (2025-11-05)
    entry4_date = datetime(2025, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    entry4 = Entry(
        title="Entry 4 - After Range",
        body="Test body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test"],
        source_author_id=source_author.id,
        project_id=project.id,
        source_created_at=entry4_date,
    )
    db.add(entry4)
    db.commit()
    db.refresh(entry4)

    # Entry 5: At the start boundary (2025-10-30T00:00:00Z)
    entry5_date = datetime(2025, 10, 30, 0, 0, 0, tzinfo=timezone.utc)
    entry5 = Entry(
        title="Entry 5 - Start Boundary",
        body="Test body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test"],
        source_author_id=source_author.id,
        project_id=project.id,
        source_created_at=entry5_date,
    )
    db.add(entry5)
    db.commit()
    db.refresh(entry5)

    # Entry 6: At the end boundary (2025-11-04T23:59:59Z)
    entry6_date = datetime(2025, 11, 4, 23, 59, 59, tzinfo=timezone.utc)
    entry6 = Entry(
        title="Entry 6 - End Boundary",
        body="Test body",
        source_id=source.id,
        external_id=str(uuid4()),
        tags=["test"],
        source_author_id=source_author.id,
        project_id=project.id,
        source_created_at=entry6_date,
    )
    db.add(entry6)
    db.commit()
    db.refresh(entry6)

    # Test the exact date range provided by the user
    search_filters = {
        "source_created_at": {
            "from": "2025-10-30T00:00:00Z",
            "to": "2025-11-04T23:59:59Z",
        },
    }

    response = client.post(
        f"/projects/{project.id}/entries/search", json=search_filters
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

    # Get the IDs of returned entries
    returned_ids = {item["id"] for item in data["items"]}

    # Entries that should be included (inside range or at boundaries)
    expected_ids = {
        str(entry1.id),  # 2025-11-01 - inside
        str(entry2.id),  # 2025-11-02 - inside
        str(entry5.id),  # 2025-10-30T00:00:00Z - start boundary
        str(entry6.id),  # 2025-11-04T23:59:59Z - end boundary
    }

    # Entries that should NOT be included (outside range)
    excluded_ids = {
        str(entry3.id),  # 2025-10-29 - before
        str(entry4.id),  # 2025-11-05 - after
    }

    # Verify all expected entries are in the results
    assert expected_ids.issubset(
        returned_ids
    ), f"Expected entries {expected_ids} not all in results {returned_ids}"

    # Verify excluded entries are NOT in the results
    assert not excluded_ids.intersection(
        returned_ids
    ), f"Excluded entries {excluded_ids} found in results {returned_ids}"

    # Test that entries before the range are excluded
    search_filters_before = {
        "source_created_at": {
            "from": "2025-10-25T00:00:00Z",
            "to": "2025-10-29T23:59:59Z",
        },
    }

    response = client.post(
        f"/projects/{project.id}/entries/search", json=search_filters_before
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids_before = {item["id"] for item in data["items"]}
    assert str(entry3.id) in returned_ids_before  # Entry 3 should be in this range
    assert (
        str(entry1.id) not in returned_ids_before
    )  # Entry 1 should NOT be in this range
    assert (
        str(entry2.id) not in returned_ids_before
    )  # Entry 2 should NOT be in this range

    # Test that entries after the range are excluded
    search_filters_after = {
        "source_created_at": {
            "from": "2025-11-05T00:00:00Z",
            "to": "2025-11-10T23:59:59Z",
        },
    }

    response = client.post(
        f"/projects/{project.id}/entries/search", json=search_filters_after
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids_after = {item["id"] for item in data["items"]}
    assert str(entry4.id) in returned_ids_after  # Entry 4 should be in this range
    assert (
        str(entry1.id) not in returned_ids_after
    )  # Entry 1 should NOT be in this range
    assert (
        str(entry2.id) not in returned_ids_after
    )  # Entry 2 should NOT be in this range
