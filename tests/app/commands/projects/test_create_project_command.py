from app.commands.projects.create_project_command import CreateProjectCommand
from app.models.project import Project
from app.models.project_membership import ProjectMembership
from app.models.workspace import Workspace
from app.schemas.project import ProjectCreate
from app.constants.membership import PROJECT_MEMBER_ROLE


class TestCreateProjectCommand:
    """Test cases for CreateProjectCommand."""

    def test_create_project_success(self, db, setup_user, setup_workspace, faker):
        """Test successfully creating a project with project membership."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
            labels={"type": "test", "priority": "high"},
        )

        # Act
        command = CreateProjectCommand(db)
        project = command.execute(project_data, user.id)

        # Assert project was created correctly
        assert project is not None
        assert project.name == project_data.name
        assert project.description == project_data.description
        assert project.workspace_id == workspace.id
        assert project.labels == project_data.labels
        assert project.id is not None

        # Assert project membership was created
        membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == PROJECT_MEMBER_ROLE
        assert membership.user_id == user.id
        assert membership.project_id == project.id

    def test_create_project_without_description(
        self, db, setup_user, setup_workspace, faker
    ):
        """Test creating a project without a description."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            workspace_id=workspace.id,
        )

        # Act
        command = CreateProjectCommand(db)
        project = command.execute(project_data, user.id)

        # Assert project was created correctly
        assert project is not None
        assert project.name == project_data.name
        assert project.description is None
        assert project.workspace_id == workspace.id

        # Assert project membership was created
        membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == PROJECT_MEMBER_ROLE

    def test_create_project_without_labels(
        self, db, setup_user, setup_workspace, faker
    ):
        """Test creating a project without labels."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
        )

        # Act
        command = CreateProjectCommand(db)
        project = command.execute(project_data, user.id)

        # Assert project was created correctly
        assert project is not None
        assert project.name == project_data.name
        assert project.description == project_data.description
        assert project.workspace_id == workspace.id
        assert project.labels == {}  # Should default to empty dict

        # Assert project membership was created
        membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == PROJECT_MEMBER_ROLE

    def test_create_project_without_workspace_id(self, db, setup_user, faker):
        """Test creating a project without workspace_id raises error."""
        # Arrange
        user = setup_user
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=None,
        )

        # Act & Assert
        command = CreateProjectCommand(db)
        try:
            command.execute(project_data, user.id)
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Workspace ID is required" in str(e)

    def test_create_project_with_nonexistent_workspace(self, db, setup_user, faker):
        """Test creating a project with non-existent workspace raises error."""
        # Arrange
        user = setup_user
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=faker.uuid4(),
        )

        # Act & Assert
        command = CreateProjectCommand(db)
        try:
            command.execute(project_data, user.id)
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Workspace with ID" in str(e)
            assert "not found" in str(e)

    def test_create_multiple_projects_same_user(
        self, db, setup_user, setup_workspace, faker
    ):
        """Test creating multiple projects for the same user."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        command = CreateProjectCommand(db)

        # Act - Create first project
        project_data_1 = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
        )
        project_1 = command.execute(project_data_1, user.id)

        # Act - Create second project
        project_data_2 = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
        )
        project_2 = command.execute(project_data_2, user.id)

        # Assert both projects were created
        assert project_1.id != project_2.id
        assert project_1.name == project_data_1.name
        assert project_2.name == project_data_2.name

        # Assert both have project memberships
        membership_1 = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project_1.id,
            )
            .first()
        )
        membership_2 = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project_2.id,
            )
            .first()
        )
        assert membership_1 is not None
        assert membership_2 is not None
        assert membership_1.role == PROJECT_MEMBER_ROLE
        assert membership_2.role == PROJECT_MEMBER_ROLE

    def test_create_projects_different_users(
        self, db, setup_user, setup_another_user, setup_workspace, faker
    ):
        """Test creating projects for different users."""
        # Arrange
        user_1 = setup_user
        user_2 = setup_another_user
        workspace = setup_workspace
        command = CreateProjectCommand(db)

        # Act - Create project for user 1
        project_data_1 = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
        )
        project_1 = command.execute(project_data_1, user_1.id)

        # Act - Create project for user 2
        project_data_2 = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
        )
        project_2 = command.execute(project_data_2, user_2.id)

        # Assert projects were created for correct users
        assert project_1.workspace_id == workspace.id
        assert project_2.workspace_id == workspace.id

        # Assert correct project memberships
        membership_1 = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user_1.id,
                ProjectMembership.project_id == project_1.id,
            )
            .first()
        )
        membership_2 = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user_2.id,
                ProjectMembership.project_id == project_2.id,
            )
            .first()
        )
        assert membership_1 is not None
        assert membership_2 is not None
        assert membership_1.role == PROJECT_MEMBER_ROLE
        assert membership_2.role == PROJECT_MEMBER_ROLE

    def test_create_project_verifies_database_persistence(
        self, db, setup_user, setup_workspace, faker
    ):
        """Test that project and membership are properly persisted in database."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
        )

        # Act
        command = CreateProjectCommand(db)
        project = command.execute(project_data, user.id)

        # Assert project exists in database
        db_project = db.query(Project).filter(Project.id == project.id).first()
        assert db_project is not None
        assert db_project.name == project_data.name
        assert db_project.description == project_data.description
        assert db_project.workspace_id == workspace.id

        # Assert membership exists in database
        db_membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert db_membership is not None
        assert db_membership.role == PROJECT_MEMBER_ROLE

    def test_create_project_with_minimal_data(
        self, db, setup_user, setup_workspace, faker
    ):
        """Test creating a project with only the required fields."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        project_data = ProjectCreate(
            name="Minimal Project",
            workspace_id=workspace.id,
        )

        # Act
        command = CreateProjectCommand(db)
        project = command.execute(project_data, user.id)

        # Assert project was created with minimal data
        assert project is not None
        assert project.name == "Minimal Project"
        assert project.description is None
        assert project.labels == {}
        assert project.workspace_id == workspace.id

        # Assert project membership was created
        membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == PROJECT_MEMBER_ROLE

    def test_create_project_with_complex_labels(
        self, db, setup_user, setup_workspace, faker
    ):
        """Test creating a project with complex labels structure."""
        # Arrange
        user = setup_user
        workspace = setup_workspace
        complex_labels = {
            "type": "web_app",
            "priority": "high",
            "team": "frontend",
            "metadata": {"version": "1.0.0", "tags": ["react", "typescript", "api"]},
            "config": {"deploy": True, "monitor": True},
        }
        project_data = ProjectCreate(
            name=faker.catch_phrase(),
            description=faker.text(100),
            workspace_id=workspace.id,
            labels=complex_labels,
        )

        # Act
        command = CreateProjectCommand(db)
        project = command.execute(project_data, user.id)

        # Assert project was created with complex labels
        assert project is not None
        assert project.name == project_data.name
        assert project.labels == complex_labels
        assert project.workspace_id == workspace.id

        # Assert project membership was created
        membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == PROJECT_MEMBER_ROLE
