def test_get_project(client, setup_project):
    """Test GET /projects/{project_id} endpoint."""
    project = setup_project
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(project.id)
    assert response.json()["name"] == project.name
    assert response.json()["description"] == project.description
    assert response.json()["workspace_id"] == str(project.workspace_id)


def test_get_nonexistent_project(client):
    """Test GET /projects/{project_id} endpoint with non-existent project."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/projects/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_update_project(client, setup_project):
    """Test PUT /projects/{project_id} endpoint."""
    project = setup_project
    update_data = {
        "name": "Updated Project Name",
        "description": "Updated project description",
    }

    response = client.put(f"/projects/{project.id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["id"] == str(project.id)
    assert response.json()["name"] == update_data["name"]
    assert response.json()["description"] == update_data["description"]


def test_update_nonexistent_project(client):
    """Test PUT /projects/{project_id} endpoint with non-existent project."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    update_data = {
        "name": "Updated Project Name",
        "description": "Updated project description",
    }

    response = client.put(f"/projects/{non_existent_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_delete_project(client, setup_project):
    """Test DELETE /projects/{project_id} endpoint."""
    project = setup_project
    response = client.delete(f"/projects/{project.id}")
    assert response.status_code == 204

    # Verify the project is deleted
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 404


def test_delete_nonexistent_project(client):
    """Test DELETE /projects/{project_id} endpoint with non-existent project."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/projects/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_project(client, setup_workspace):
    """Test POST /workspaces/{workspace_id}/projects endpoint."""
    workspace = setup_workspace
    project_data = {
        "name": "Test Project",
        "description": "A test project description",
    }

    response = client.post(f"/workspaces/{workspace.id}/projects", json=project_data)
    assert response.status_code == 201
    project = response.json()
    assert project["name"] == project_data["name"]
    assert project["description"] == project_data["description"]
    assert project["workspace_id"] == str(workspace.id)


def test_create_project_nonexistent_workspace(client):
    """Test POST /workspaces/{workspace_id}/projects endpoint with non-existent workspace."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    project_data = {"name": "Test Project", "description": "A test project description"}

    response = client.post(f"/workspaces/{non_existent_id}/projects", json=project_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_create_project_invalid_data(client, setup_workspace):
    """Test POST /workspaces/{workspace_id}/projects endpoint with invalid data."""
    workspace = setup_workspace
    invalid_project_data = {
        "name": "",  # Empty name should be invalid
        "description": "A test project description",
    }

    response = client.post(
        f"/workspaces/{workspace.id}/projects", json=invalid_project_data
    )
    assert response.status_code == 422  # Validation error


def test_list_projects(client, setup_project):
    """Test GET /workspaces/{workspace_id}/projects endpoint."""
    project = setup_project
    response = client.get(f"/workspaces/{project.workspace_id}/projects")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    # Verify the created project is in the list
    project_list = data["data"]
    assert any(p["id"] == str(project.id) for p in project_list)
    assert any(p["name"] == project.name for p in project_list)
    assert any(p["description"] == project.description for p in project_list)


def test_search_projects_exact_match(client, setup_project):
    """Test POST /projects/search endpoint with exact match."""
    project = setup_project
    search_filters = {"name": project.name, "workspace_id": str(project.workspace_id)}

    response = client.post("/projects/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    results = data["data"]
    assert len(results) == 1
    assert results[0]["id"] == str(project.id)
    assert results[0]["name"] == project.name


def test_search_projects_partial_match(client, setup_project):
    """Test POST /projects/search endpoint with partial match using ilike."""
    project = setup_project
    # Search for part of the project name
    partial_name = project.name[: len(project.name) // 2]
    search_filters = {"name": {"operator": "ilike", "value": f"%{partial_name}%"}}

    response = client.post("/projects/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    results = data["data"]
    assert len(results) > 0
    assert any(p["id"] == str(project.id) for p in results)


def test_search_projects_no_matches(client):
    """Test POST /projects/search endpoint with no matching results."""
    search_filters = {"name": "NonExistentProjectName123"}

    response = client.post("/projects/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    results = data["data"]
    assert len(results) == 0


def test_search_projects_multiple_conditions(client, setup_project):
    """Test POST /projects/search endpoint with multiple search conditions."""
    project = setup_project
    search_filters = {
        "name": {"operator": "ilike", "value": f"%{project.name}%"},
        "workspace_id": str(project.workspace_id),
    }

    response = client.post("/projects/search", json=search_filters)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    results = data["data"]
    assert len(results) == 1
    assert results[0]["id"] == str(project.id)


def test_search_projects_invalid_operator(client):
    """Test POST /projects/search endpoint with invalid operator."""
    search_filters = {"name": {"operator": "invalid_operator", "value": "test"}}

    response = client.post("/projects/search", json=search_filters)
    assert response.status_code == 422  # Validation error


def test_delete_project_membership(client, setup_project_membership):
    """Test DELETE /projects/{project_id}/memberships/{membership_id} endpoint."""
    membership = setup_project_membership

    # Delete membership
    response = client.delete(
        f"/projects/{membership.project_id}/memberships/{membership.id}"
    )
    assert response.status_code == 204

    # Verify membership no longer appears in the project's membership list
    list_response = client.get(f"/projects/{membership.project_id}/memberships")
    assert list_response.status_code == 200
    data = list_response.json()
    assert "data" in data
    assert all(m["id"] != str(membership.id) for m in data["data"])


def test_delete_project_membership_not_found(client, setup_project):
    """Test DELETE /projects/{project_id}/memberships/{membership_id} with non-existent membership."""
    project = setup_project
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.delete(f"/projects/{project.id}/memberships/{fake_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project membership not found"


def test_get_project_membership(client, setup_project_membership):
    """Test GET /projects/{project_id}/memberships/{membership_id} endpoint."""
    membership = setup_project_membership

    response = client.get(
        f"/projects/{membership.project_id}/memberships/{membership.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(membership.id)
    assert data["user_id"] == str(membership.user_id)
    assert data["project_id"] == str(membership.project_id)
    assert data["role"] == membership.role


def test_get_project_membership_not_found(client, setup_project):
    """Test GET /projects/{project_id}/memberships/{membership_id} with non-existent membership."""
    project = setup_project
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/projects/{project.id}/memberships/{fake_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project membership not found"


def test_import_items_success(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with valid data."""
    project = setup_project

    # Test payload from user request
    payload = {
        "items": [
            {
                "source": "github",
                "title": "API returns 500 error on POST /users",
                "body": "Steps to reproduce:\n1. Send POST request to /users with valid payload\n2. Server responds with 500 instead of 201",
                "tags": ["bug", "api"],
                "labels": {"priority": "high"},
                "meta_data": {"repo": "org/repo"},
                "author": {
                    "id": "9876543210",
                    "display_name": "Alice Smith",
                    "avatar_url": "https://avatar.url/alice",
                    "email": "alice.smith@example.com",
                    "tags": ["bug", "api"],
                    "labels": {"priority": "high"},
                    "meta_data": {"source": "github"},
                },
            },
            {
                "source": "github",
                "title": "UI freezes when loading dashboard",
                "body": "The dashboard page becomes unresponsive when more than 1000 records are loaded. Needs optimization.",
                "tags": ["bug", "frontend"],
                "labels": {"priority": "medium"},
                "meta_data": {"repo": "org/repo"},
                "author": {
                    "id": "2468013579",
                    "display_name": "Bob Johnson",
                    "avatar_url": "https://avatar.url/bob",
                    "email": "bob.johnson@example.com",
                    "tags": ["bug", "frontend"],
                    "labels": {"priority": "medium"},
                    "meta_data": {"source": "github"},
                },
            },
            {
                "source": "github",
                "title": "Add dark mode support",
                "body": "Feature request: Implement dark mode toggle in settings. Many users have asked for this.",
                "tags": ["enhancement", "ui"],
                "labels": {"priority": "low"},
                "meta_data": {"repo": "org/repo"},
                "author": {
                    "id": "1122334455",
                    "display_name": "Charlie Lee",
                    "avatar_url": "https://avatar.url/charlie",
                    "email": "charlie.lee@example.com",
                    "tags": ["enhancement", "ui"],
                    "labels": {"priority": "low"},
                    "meta_data": {"source": "github"},
                },
            },
        ]
    }

    response = client.post(f"/projects/{project.id}/import", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "import_request_id" in data
    assert "total_items" in data
    assert "processed_items" in data
    assert "success_count" in data
    assert "failure_count" in data
    assert "status" in data

    # Verify response values
    assert data["total_items"] == 3
    assert data["processed_items"] == 3
    assert data["success_count"] == 3
    assert data["failure_count"] == 0
    assert data["status"] == "completed"


def test_import_items_empty_list(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with empty items list."""
    project = setup_project

    payload = {"items": []}

    response = client.post(f"/projects/{project.id}/import", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_items"] == 0
    assert data["processed_items"] == 0
    assert data["success_count"] == 0
    assert data["failure_count"] == 0
    assert data["status"] == "completed"


def test_import_items_single_item(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with single item."""
    project = setup_project

    payload = {
        "items": [
            {
                "source": "github",
                "title": "Single test item",
                "body": "This is a test item",
                "tags": ["test"],
                "labels": {"priority": "low"},
                "meta_data": {"repo": "test/repo"},
                "author": {
                    "id": "123456789",
                    "display_name": "Test Author",
                    "avatar_url": "https://example.com/avatar",
                    "email": "test@example.com",
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"source": "github"},
                },
            }
        ]
    }

    response = client.post(f"/projects/{project.id}/import", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_items"] == 1
    assert data["processed_items"] == 1
    assert data["success_count"] == 1
    assert data["failure_count"] == 0
    assert data["status"] == "completed"


def test_import_items_nonexistent_project(client):
    """Test POST /projects/{project_id}/import endpoint with non-existent project."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    payload = {
        "items": [
            {
                "source": "github",
                "title": "Test item",
                "body": "Test body",
                "tags": ["test"],
                "labels": {"priority": "low"},
                "meta_data": {"repo": "test/repo"},
                "author": {
                    "id": "123456789",
                    "display_name": "Test Author",
                    "avatar_url": "https://example.com/avatar",
                    "email": "test@example.com",
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"source": "github"},
                },
            }
        ]
    }

    response = client.post(f"/projects/{non_existent_id}/import", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_import_items_invalid_payload(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with invalid payload."""
    project = setup_project

    # Missing required fields
    invalid_payload = {
        "items": [
            {
                "source": "github",
                "title": "Test item",
                # Missing body, tags, labels, meta_data, author
            }
        ]
    }

    response = client.post(f"/projects/{project.id}/import", json=invalid_payload)
    assert response.status_code == 422  # Validation error


def test_import_items_invalid_author_data(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with invalid author data."""
    project = setup_project

    payload = {
        "items": [
            {
                "source": "github",
                "title": "Test item",
                "body": "Test body",
                "tags": ["test"],
                "labels": {"priority": "low"},
                "meta_data": {"repo": "test/repo"},
                "author": {
                    "id": "123456789",
                    # Missing required fields: display_name, avatar_url, email
                    "tags": ["test"],
                    "labels": {"priority": "low"},
                    "meta_data": {"source": "github"},
                },
            }
        ]
    }

    response = client.post(f"/projects/{project.id}/import", json=payload)
    assert response.status_code == 422  # Validation error


def test_import_items_minimal_data(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with minimal required data."""
    project = setup_project

    payload = {
        "items": [
            {
                "source": "github",
                "title": "Minimal item",
                "body": "Minimal test item",
                "tags": [],
                "labels": {},
                "meta_data": {},
                "author": {
                    "id": "555555555",
                    "display_name": "Minimal Author",
                    "avatar_url": "https://example.com/minimal",
                    "email": "minimal@example.com",
                    "tags": [],
                    "labels": {},
                    "meta_data": {},
                },
            }
        ]
    }

    response = client.post(f"/projects/{project.id}/import", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success_count"] == 1
    assert data["failure_count"] == 0
    assert data["status"] == "completed"


def test_import_items_multiple_items(client, setup_project):
    """Test POST /projects/{project_id}/import endpoint with multiple items."""
    project = setup_project

    payload = {
        "items": [
            {
                "source": "github",
                "title": "First item",
                "body": "First test item",
                "tags": ["test", "first"],
                "labels": {"priority": "high"},
                "meta_data": {"repo": "test/repo", "issue": "1"},
                "author": {
                    "id": "111111111",
                    "display_name": "First Author",
                    "avatar_url": "https://example.com/avatar1",
                    "email": "first@example.com",
                    "tags": ["test", "first"],
                    "labels": {"priority": "high"},
                    "meta_data": {"source": "github"},
                },
            },
            {
                "source": "github",
                "title": "Second item",
                "body": "Second test item",
                "tags": ["test", "second"],
                "labels": {"priority": "medium"},
                "meta_data": {"repo": "test/repo", "issue": "2"},
                "author": {
                    "id": "222222222",
                    "display_name": "Second Author",
                    "avatar_url": "https://example.com/avatar2",
                    "email": "second@example.com",
                    "tags": ["test", "second"],
                    "labels": {"priority": "medium"},
                    "meta_data": {"source": "github"},
                },
            },
        ]
    }

    response = client.post(f"/projects/{project.id}/import", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_items"] == 2
    assert data["processed_items"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0
    assert data["status"] == "completed"
