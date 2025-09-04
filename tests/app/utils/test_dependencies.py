import pytest
from uuid import uuid4
from fastapi import HTTPException
from app.routers.utils.dependencies import get_project_by_id


def test_get_project_by_id_success(db, setup_project):
    """Test successful retrieval of a project by ID."""
    project = setup_project
    retrieved_project = get_project_by_id(project.id, db)

    assert retrieved_project.id == project.id
    assert retrieved_project.name == project.name
    assert retrieved_project.description == project.description
    assert retrieved_project.workspace_id == project.workspace_id


def test_get_project_by_id_not_found(db):
    """Test that a 404 error is raised when project is not found."""
    non_existent_id = uuid4()
    with pytest.raises(HTTPException) as exc_info:
        get_project_by_id(non_existent_id, db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"
