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
