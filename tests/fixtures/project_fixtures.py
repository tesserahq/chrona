import pytest
from app.models.project import Project
from sqlalchemy.orm import Session


@pytest.fixture
def setup_project(db: Session, setup_workspace, faker):
    """Create a test project in the database with optional overrides."""
    workspace = setup_workspace

    project_data = {
        "name": faker.company(),
        "description": faker.text(100),
        "workspace_id": workspace.id,
    }

    project = Project(**project_data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
