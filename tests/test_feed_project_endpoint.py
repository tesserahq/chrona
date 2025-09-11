from fastapi.testclient import TestClient
from uuid import uuid4

from app.models.project import Project


def test_feed_project_endpoint_success(client: TestClient, setup_project: Project):
    """Test successful project feeding."""
    response = client.post(
        f"/projects/{setup_project.id}/feed",
        json={"num_entries": 5, "num_digests": 3},  # Small number for testing
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "Successfully fed project" in data["message"]
    assert data["entries_created"] == 5
    assert data["digests_created"] == 3
    assert data["authors_created"] > 0
    assert data["entry_updates_created"] > 0
    assert data["digest_configs_created"] == 3


def test_feed_project_endpoint_project_not_found(client: TestClient):
    """Test feeding a non-existent project."""
    fake_project_id = uuid4()
    response = client.post(
        f"/projects/{fake_project_id}/feed", json={"num_entries": 5, "num_digests": 3}
    )

    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_feed_project_endpoint_default_values(
    client: TestClient, setup_project: Project
):
    """Test feeding project with default values."""
    response = client.post(f"/projects/{setup_project.id}/feed", json={})

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["entries_created"] == 50  # Default value
    assert data["digests_created"] == 20  # Default value


def test_feed_project_endpoint_custom_values(
    client: TestClient, setup_project: Project
):
    """Test feeding project with custom values."""
    response = client.post(
        f"/projects/{setup_project.id}/feed", json={"num_entries": 10, "num_digests": 5}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["entries_created"] == 10
    assert data["digests_created"] == 5
