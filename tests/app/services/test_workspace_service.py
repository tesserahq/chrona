import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.workspace_service import WorkspaceService


@pytest.fixture
def sample_workspace_data():
    return {"name": "Test Workspace", "description": "A test workspace"}


def test_create_workspace(db: Session, setup_user, sample_workspace_data):
    # Create workspace
    user = setup_user
    sample_workspace_data = {**sample_workspace_data, "created_by_id": user.id}
    workspace_create = WorkspaceCreate(**sample_workspace_data)
    workspace = WorkspaceService(db).create_workspace(workspace_create)

    # Assertions
    assert workspace.id is not None
    assert workspace.name == sample_workspace_data["name"]
    assert workspace.description == sample_workspace_data["description"]
    assert workspace.created_by_id == sample_workspace_data["created_by_id"]
    assert workspace.created_at is not None
    assert workspace.updated_at is not None


def test_get_workspace(db: Session, setup_workspace):
    workspace = setup_workspace

    # Get workspace
    retrieved_workspace = WorkspaceService(db).get_workspace(workspace.id)

    # Assertions
    assert retrieved_workspace is not None
    assert retrieved_workspace.id == workspace.id
    assert retrieved_workspace.name == workspace.name


def test_get_workspace_not_found(db: Session):
    # Try to get non-existent workspace
    retrieved_workspace = WorkspaceService(db).get_workspace(uuid4())

    # Assertion
    assert retrieved_workspace is None


def test_get_workspaces(db: Session, setup_workspace):
    workspace = setup_workspace

    # Get all workspaces
    workspaces = WorkspaceService(db).get_workspaces()

    # Assertions
    assert len(workspaces) >= 1
    assert any(w.id == workspace.id for w in workspaces)


def test_update_workspace(db: Session, setup_workspace):
    workspace = setup_workspace

    # Update data
    update_data = {"name": "Updated Workspace", "description": "Updated description"}
    workspace_update = WorkspaceUpdate(**update_data)

    # Update workspace
    updated_workspace = WorkspaceService(db).update_workspace(
        workspace.id, workspace_update
    )

    # Assertions
    assert updated_workspace is not None
    assert updated_workspace.id == workspace.id
    assert updated_workspace.name == update_data["name"]
    assert updated_workspace.description == update_data["description"]


def test_update_workspace_not_found(db: Session):
    # Try to update non-existent workspace
    update_data = {"name": "Updated Workspace"}
    workspace_update = WorkspaceUpdate(**update_data)

    # Update workspace
    updated_workspace = WorkspaceService(db).update_workspace(uuid4(), workspace_update)

    # Assertion
    assert updated_workspace is None


def test_delete_workspace(db: Session, setup_workspace):
    workspace = setup_workspace

    # Delete workspace
    workspace_service = WorkspaceService(db)
    success = workspace_service.delete_workspace(workspace.id)

    # Assertions
    assert success is True
    deleted_workspace = workspace_service.get_workspace(workspace.id)
    assert deleted_workspace is None


def test_delete_workspace_not_found(db: Session):
    # Try to delete non-existent workspace
    success = WorkspaceService(db).delete_workspace(uuid4())

    # Assertion
    assert success is False


def test_search_workspaces_with_filters(db: Session, setup_workspace):
    workspace = setup_workspace

    # Search using ilike filter
    filters = {"name": {"operator": "ilike", "value": f"%{workspace.name}%"}}
    results = WorkspaceService(db).search(filters)

    assert isinstance(results, list)
    assert any(result.id == workspace.id for result in results)

    # Search using exact match
    filters = {"name": workspace.name}
    results = WorkspaceService(db).search(filters)

    assert len(results) == 1
    assert results[0].id == workspace.id

    # Search with no match
    filters = {"name": {"operator": "==", "value": "Nonexistent Name"}}
    results = WorkspaceService(db).search(filters)

    assert len(results) == 0


def test_create_workspace_with_identifier(db: Session, setup_user):
    """Test creating a workspace with an identifier field."""
    user = setup_user

    # Create workspace data with identifier
    workspace_data = {
        "name": "Test Workspace with Identifier",
        "description": "A test workspace with identifier",
        "identifier": "test-workspace-123",
        "created_by_id": user.id,
    }

    workspace_create = WorkspaceCreate(**workspace_data)
    workspace = WorkspaceService(db).create_workspace(workspace_create)

    # Assertions
    assert workspace.id is not None
    assert workspace.name == workspace_data["name"]
    assert workspace.description == workspace_data["description"]
    assert workspace.identifier == workspace_data["identifier"]
    assert workspace.created_by_id == workspace_data["created_by_id"]
    assert workspace.created_at is not None
    assert workspace.updated_at is not None


def test_create_workspace_with_duplicate_identifier(db: Session, setup_user):
    """Test that creating a workspace with a duplicate identifier fails."""
    user = setup_user

    # Create first workspace with identifier
    workspace_data_1 = {
        "name": "First Workspace",
        "description": "First workspace with identifier",
        "identifier": "duplicate-identifier",
        "created_by_id": user.id,
    }

    workspace_create_1 = WorkspaceCreate(**workspace_data_1)
    workspace_1 = WorkspaceService(db).create_workspace(workspace_create_1)

    # Try to create second workspace with same identifier
    workspace_data_2 = {
        "name": "Second Workspace",
        "description": "Second workspace with same identifier",
        "identifier": "duplicate-identifier",
        "created_by_id": user.id,
    }

    workspace_create_2 = WorkspaceCreate(**workspace_data_2)

    # This should raise an integrity error due to unique constraint
    with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
        WorkspaceService(db).create_workspace(workspace_create_2)


def test_update_workspace_with_identifier(db: Session, setup_workspace):
    """Test updating a workspace with an identifier field."""
    workspace = setup_workspace

    # Update data including identifier
    update_data = {
        "name": "Updated Workspace with Identifier",
        "description": "Updated description with identifier",
        "identifier": "updated-workspace-456",
    }
    workspace_update = WorkspaceUpdate(**update_data)

    # Update workspace
    updated_workspace = WorkspaceService(db).update_workspace(
        workspace.id, workspace_update
    )

    # Assertions
    assert updated_workspace is not None
    assert updated_workspace.id == workspace.id
    assert updated_workspace.name == update_data["name"]
    assert updated_workspace.description == update_data["description"]
    assert updated_workspace.identifier == update_data["identifier"]


def test_search_workspaces_by_identifier(db: Session, setup_user):
    """Test searching workspaces by identifier field."""
    user = setup_user

    # Create workspace with identifier
    workspace_data = {
        "name": "Searchable Workspace",
        "description": "A workspace for testing search",
        "identifier": "searchable-workspace",
        "created_by_id": user.id,
    }

    workspace_create = WorkspaceCreate(**workspace_data)
    workspace = WorkspaceService(db).create_workspace(workspace_create)

    # Search by exact identifier match
    filters = {"identifier": "searchable-workspace"}
    results = WorkspaceService(db).search(filters)

    assert len(results) == 1
    assert results[0].id == workspace.id
    assert results[0].identifier == workspace_data["identifier"]

    # Search by partial identifier match
    filters = {"identifier": {"operator": "ilike", "value": "%searchable%"}}
    results = WorkspaceService(db).search(filters)

    assert len(results) == 1
    assert results[0].id == workspace.id


def test_get_workspace_stats_empty_workspace(db: Session, setup_workspace):
    """Test get_workspace_stats with an empty workspace."""
    workspace = setup_workspace

    stats = WorkspaceService(db).get_workspace_stats(workspace.id)

    assert stats is not None
    assert stats.project_stats.total_projects == 0
    assert stats.project_stats.recent_projects == []


def test_get_workspace_stats_with_projects(db: Session, setup_workspace, setup_project):
    """Test get_workspace_stats with projects."""
    workspace = setup_workspace
    project = setup_project

    stats = WorkspaceService(db).get_workspace_stats(workspace.id)

    assert stats is not None
    assert stats.project_stats.total_projects == 1
    assert len(stats.project_stats.recent_projects) == 1
    assert stats.project_stats.recent_projects[0].id == project.id
    assert stats.project_stats.recent_projects[0].name == project.name
    assert stats.project_stats.recent_projects[0].description == project.description


def test_get_workspace_stats_comprehensive(
    db: Session,
    setup_workspace,
    setup_project,
):
    """Test get_workspace_stats with all types of data."""
    workspace = setup_workspace
    project = setup_project

    stats = WorkspaceService(db).get_workspace_stats(workspace.id)

    assert stats is not None

    # Check projects
    assert stats.project_stats.total_projects == 1
    assert len(stats.project_stats.recent_projects) == 1
    assert stats.project_stats.recent_projects[0].id == project.id


def test_get_workspace_stats_multiple_items(db: Session, setup_workspace, faker):
    """Test get_workspace_stats with multiple items."""
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

    stats = WorkspaceService(db).get_workspace_stats(workspace.id)

    assert stats is not None

    # Check counts
    assert stats.project_stats.total_projects == 3

    # Check recent items (should be limited to 5 most recent)
    assert len(stats.project_stats.recent_projects) == 3


def test_get_workspace_stats_nonexistent_workspace(db: Session):
    """Test get_workspace_stats with nonexistent workspace."""
    import uuid

    nonexistent_id = uuid.uuid4()
    stats = WorkspaceService(db).get_workspace_stats(nonexistent_id)

    assert stats is None


def test_get_workspace_stats_recent_items_limit(db: Session, setup_workspace, faker):
    """Test get_workspace_stats ensures recent items are limited to 5."""
    workspace = setup_workspace

    # Create more than 5 projects
    from app.models.project import Project

    for i in range(7):
        project = Project(
            name=f"Project {i}",
            description=f"Description {i}",
            workspace_id=workspace.id,
        )
        db.add(project)

    db.commit()

    stats = WorkspaceService(db).get_workspace_stats(workspace.id)

    assert stats is not None
    assert stats.project_stats.total_projects == 7
    assert len(stats.project_stats.recent_projects) == 5  # Limited to 5
