def test_list_workspaces(client, setup_workspace, setup_different_workspace):
    """Test GET /workspaces endpoint."""
    workspace = setup_workspace
    _ = setup_different_workspace

    # Ensure the workspace is created
    response = client.get("/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)

    # Make sure the response contains the correct workspace
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == str(workspace.id)
    assert data["data"][0]["name"] == workspace.name
    assert data["data"][0]["description"] == workspace.description
    assert data["data"][0]["created_by_id"] == str(workspace.created_by_id)


def test_get_workspace(client, setup_workspace):
    """Test GET /workspaces/{workspace_id} endpoint."""
    workspace = setup_workspace
    response = client.get(f"/workspaces/{workspace.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(workspace.id)
    assert response.json()["name"] == workspace.name
    assert response.json()["description"] == workspace.description
    assert response.json()["created_by_id"] == str(workspace.created_by_id)


def test_create_workspace(client, setup_user):
    """Test POST /workspaces endpoint."""

    user = setup_user

    response = client.post(
        "/workspaces",
        json={"name": "Test Workspace"},
    )
    assert response.status_code == 201
    workspace = response.json()
    assert workspace["name"] == "Test Workspace"
    assert workspace["created_by_id"] == str(user.id)

    # Verify that a membership was created for the workspace creator
    workspace_id = workspace["id"]
    membership_response = client.get(f"/workspaces/{workspace_id}/memberships")
    assert membership_response.status_code == 200

    memberships = membership_response.json()["data"]
    assert len(memberships) == 1

    membership = memberships[0]
    assert membership["user_id"] == str(user.id)
    assert membership["workspace_id"] == workspace_id
    assert membership["role"] == "owner"  # Should be owner role


def test_create_workspace_invalid_data(client, setup_user):
    """Test POST /workspaces endpoint with invalid data."""
    invalid_workspace_data = {
        "name": "",  # Empty name should be invalid
        "description": "A test workspace description",
    }

    response = client.post("/workspaces", json=invalid_workspace_data)
    assert response.status_code == 422  # Validation error


def test_create_workspace_missing_name(client, setup_user):
    """Test POST /workspaces endpoint with missing name field."""
    invalid_workspace_data = {
        "description": "A test workspace description",
        # Missing 'name' field
    }

    response = client.post("/workspaces", json=invalid_workspace_data)
    assert response.status_code == 422  # Validation error


def test_update_workspace_invalid_data(client, setup_workspace):
    """Test PUT /workspaces/{workspace_id} endpoint with invalid data."""
    workspace = setup_workspace
    invalid_update_data = {
        "name": "",  # Empty name should be invalid
        "description": "Updated description",
    }

    response = client.put(f"/workspaces/{workspace.id}", json=invalid_update_data)
    assert response.status_code == 422  # Validation error


def test_delete_workspace(client, setup_workspace):
    """Test DELETE /workspaces/{workspace_id} endpoint."""
    workspace = setup_workspace
    response = client.delete(f"/workspaces/{workspace.id}")
    assert response.status_code == 204

    # Verify the workspace is deleted
    response = client.get(f"/workspaces/{workspace.id}")
    assert response.status_code == 404


def test_delete_locked_workspace(client, setup_workspace):
    """Test DELETE /workspaces/{workspace_id} endpoint with locked workspace."""
    workspace = setup_workspace

    # First lock the workspace
    update_response = client.put(f"/workspaces/{workspace.id}", json={"locked": True})
    assert update_response.status_code == 200
    assert update_response.json()["locked"] is True

    # Try to delete the locked workspace - should fail
    response = client.delete(f"/workspaces/{workspace.id}")
    assert response.status_code == 400
    assert "is locked and cannot be deleted" in response.json()["detail"]

    # Verify the workspace still exists
    response = client.get(f"/workspaces/{workspace.id}")
    assert response.status_code == 200
    assert response.json()["locked"] is True


def test_update_workspace_locked_field(client, setup_workspace):
    """Test PUT /workspaces/{workspace_id} endpoint to update locked field."""
    workspace = setup_workspace

    # Lock the workspace
    response = client.put(f"/workspaces/{workspace.id}", json={"locked": True})
    assert response.status_code == 200
    updated_workspace = response.json()
    assert updated_workspace["locked"] is True
    assert updated_workspace["id"] == str(workspace.id)

    # Unlock the workspace
    response = client.put(f"/workspaces/{workspace.id}", json={"locked": False})
    assert response.status_code == 200
    updated_workspace = response.json()
    assert updated_workspace["locked"] is False

    # Verify we can now delete the unlocked workspace
    response = client.delete(f"/workspaces/{workspace.id}")
    assert response.status_code == 204


def test_create_workspace_with_locked_field(client, setup_user):
    """Test POST /workspaces endpoint with locked field."""
    user = setup_user

    response = client.post(
        "/workspaces",
        json={"name": "Test Locked Workspace", "locked": True},
    )
    assert response.status_code == 201
    workspace = response.json()
    assert workspace["name"] == "Test Locked Workspace"
    assert workspace["locked"] is True
    assert workspace["created_by_id"] == str(user.id)

    # Try to delete the locked workspace - should fail
    workspace_id = workspace["id"]
    delete_response = client.delete(f"/workspaces/{workspace_id}")
    assert delete_response.status_code == 400
    assert "is locked and cannot be deleted" in delete_response.json()["detail"]


def test_get_workspace_stats_empty_workspace(client, setup_workspace):
    """Test GET /workspaces/{workspace_id}/stats endpoint with empty workspace."""
    workspace = setup_workspace
    response = client.get(f"/workspaces/{workspace.id}/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["project_stats"]["total_projects"] == 0
    assert data["project_stats"]["recent_projects"] == []


def test_get_workspace_stats_with_projects(client, setup_workspace, setup_project):
    """Test GET /workspaces/{workspace_id}/stats endpoint with projects."""
    workspace = setup_workspace
    project = setup_project

    response = client.get(f"/workspaces/{workspace.id}/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["project_stats"]["total_projects"] == 1
    assert len(data["project_stats"]["recent_projects"]) == 1
    assert data["project_stats"]["recent_projects"][0]["id"] == str(project.id)
    assert data["project_stats"]["recent_projects"][0]["name"] == project.name
    assert (
        data["project_stats"]["recent_projects"][0]["description"]
        == project.description
    )


def test_get_workspace_stats_comprehensive(client, setup_workspace, setup_project):
    """Test GET /workspaces/{workspace_id}/stats endpoint with all types of data."""
    workspace = setup_workspace
    project = setup_project

    response = client.get(f"/workspaces/{workspace.id}/stats")
    assert response.status_code == 200

    data = response.json()

    # Check projects
    assert data["project_stats"]["total_projects"] == 1
    assert len(data["project_stats"]["recent_projects"]) == 1
    assert data["project_stats"]["recent_projects"][0]["id"] == str(project.id)


def test_get_workspace_stats_multiple_items(client, setup_workspace, db, faker):
    """Test GET /workspaces/{workspace_id}/stats endpoint with multiple items."""
    workspace = setup_workspace

    # Create multiple projects
    from app.models.project import Project

    projects = []
    for i in range(3):
        project = Project(
            name=f"Project {i}",
            description=f"Description {i}",
            workspace_id=workspace.id,
        )
        db.add(project)
        projects.append(project)

    response = client.get(f"/workspaces/{workspace.id}/stats")
    assert response.status_code == 200

    data = response.json()

    # Check counts
    assert data["project_stats"]["total_projects"] == 3

    # Check recent items (should be limited to 5 most recent)
    assert len(data["project_stats"]["recent_projects"]) == 3


def test_get_workspace_stats_nonexistent_workspace(client):
    """Test GET /workspaces/{workspace_id}/stats endpoint with nonexistent workspace."""
    import uuid

    nonexistent_id = uuid.uuid4()
    response = client.get(f"/workspaces/{nonexistent_id}/stats")
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_get_workspace_stats_different_workspace(client, setup_different_workspace):
    """Test GET /workspaces/{workspace_id}/stats endpoint with a different workspace."""
    workspace = setup_different_workspace

    response = client.get(f"/workspaces/{workspace.id}/stats")
    assert response.status_code == 200

    # Should return empty stats for the different workspace
    data = response.json()
    assert data["project_stats"]["total_projects"] == 0
    assert data["project_stats"]["recent_projects"] == []
