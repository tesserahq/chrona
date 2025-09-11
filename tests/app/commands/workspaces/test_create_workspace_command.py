from app.commands.workspaces.create_workspace_command import CreateWorkspaceCommand
from app.models.workspace import Workspace
from app.models.membership import Membership
from app.schemas.workspace import WorkspaceCreate
from app.constants.membership import OWNER_ROLE


class TestCreateWorkspaceCommand:
    """Test cases for CreateWorkspaceCommand."""

    def test_create_workspace_success(self, db, setup_user, faker):
        """Test successfully creating a workspace with owner membership."""
        # Arrange
        user = setup_user
        workspace_data = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=user.id,
        )

        # Act
        command = CreateWorkspaceCommand(db)
        workspace = command.execute(workspace_data)

        # Assert workspace was created correctly
        assert workspace is not None
        assert workspace.name == workspace_data.name
        assert workspace.description == workspace_data.description
        assert workspace.created_by_id == user.id
        assert workspace.id is not None

        # Assert owner membership was created
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == OWNER_ROLE
        assert membership.user_id == user.id
        assert membership.workspace_id == workspace.id

    def test_create_workspace_without_description(self, db, setup_user, faker):
        """Test creating a workspace without a description."""
        # Arrange
        user = setup_user
        workspace_data = WorkspaceCreate(
            name=faker.company(),
            created_by_id=user.id,
        )

        # Act
        command = CreateWorkspaceCommand(db)
        workspace = command.execute(workspace_data)

        # Assert workspace was created correctly
        assert workspace is not None
        assert workspace.name == workspace_data.name
        assert workspace.description is None
        assert workspace.created_by_id == user.id

        # Assert owner membership was created
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == OWNER_ROLE

    def test_create_workspace_with_identifier(self, db, setup_user, faker):
        """Test creating a workspace with an identifier."""
        # Arrange
        user = setup_user
        workspace_data = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            identifier="test-workspace-123",
            created_by_id=user.id,
        )

        # Act
        command = CreateWorkspaceCommand(db)
        workspace = command.execute(workspace_data)

        # Assert workspace was created correctly
        assert workspace is not None
        assert workspace.name == workspace_data.name
        assert workspace.identifier == "test-workspace-123"
        assert workspace.created_by_id == user.id

        # Assert owner membership was created
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == OWNER_ROLE

    def test_create_workspace_with_logo(self, db, setup_user, faker):
        """Test creating a workspace with a logo URL."""
        # Arrange
        user = setup_user
        workspace_data = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            logo="https://example.com/logo.png",
            created_by_id=user.id,
        )

        # Act
        command = CreateWorkspaceCommand(db)
        workspace = command.execute(workspace_data)

        # Assert workspace was created correctly
        assert workspace is not None
        assert workspace.name == workspace_data.name
        assert workspace.logo == "https://example.com/logo.png"
        assert workspace.created_by_id == user.id

        # Assert owner membership was created
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == OWNER_ROLE

    def test_create_multiple_workspaces_same_user(self, db, setup_user, faker):
        """Test creating multiple workspaces for the same user."""
        # Arrange
        user = setup_user
        command = CreateWorkspaceCommand(db)

        # Act - Create first workspace
        workspace_data_1 = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=user.id,
        )
        workspace_1 = command.execute(workspace_data_1)

        # Act - Create second workspace
        workspace_data_2 = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=user.id,
        )
        workspace_2 = command.execute(workspace_data_2)

        # Assert both workspaces were created
        assert workspace_1.id != workspace_2.id
        assert workspace_1.name == workspace_data_1.name
        assert workspace_2.name == workspace_data_2.name

        # Assert both have owner memberships
        membership_1 = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace_1.id,
            )
            .first()
        )
        membership_2 = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace_2.id,
            )
            .first()
        )
        assert membership_1 is not None
        assert membership_2 is not None
        assert membership_1.role == OWNER_ROLE
        assert membership_2.role == OWNER_ROLE

    def test_create_workspace_different_users(
        self, db, setup_user, setup_another_user, faker
    ):
        """Test creating workspaces for different users."""
        # Arrange
        user_1 = setup_user
        user_2 = setup_another_user
        command = CreateWorkspaceCommand(db)

        # Act - Create workspace for user 1
        workspace_data_1 = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=user_1.id,
        )
        workspace_1 = command.execute(workspace_data_1)

        # Act - Create workspace for user 2
        workspace_data_2 = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=user_2.id,
        )
        workspace_2 = command.execute(workspace_data_2)

        # Assert workspaces were created for correct users
        assert workspace_1.created_by_id == user_1.id
        assert workspace_2.created_by_id == user_2.id

        # Assert correct owner memberships
        membership_1 = (
            db.query(Membership)
            .filter(
                Membership.user_id == user_1.id,
                Membership.workspace_id == workspace_1.id,
            )
            .first()
        )
        membership_2 = (
            db.query(Membership)
            .filter(
                Membership.user_id == user_2.id,
                Membership.workspace_id == workspace_2.id,
            )
            .first()
        )
        assert membership_1 is not None
        assert membership_2 is not None
        assert membership_1.role == OWNER_ROLE
        assert membership_2.role == OWNER_ROLE

    def test_create_workspace_verifies_database_persistence(
        self, db, setup_user, faker
    ):
        """Test that workspace and membership are properly persisted in database."""
        # Arrange
        user = setup_user
        workspace_data = WorkspaceCreate(
            name=faker.company(),
            description=faker.text(100),
            created_by_id=user.id,
        )

        # Act
        command = CreateWorkspaceCommand(db)
        workspace = command.execute(workspace_data)

        # Assert workspace exists in database
        db_workspace = db.query(Workspace).filter(Workspace.id == workspace.id).first()
        assert db_workspace is not None
        assert db_workspace.name == workspace_data.name
        assert db_workspace.description == workspace_data.description
        assert db_workspace.created_by_id == user.id

        # Assert membership exists in database
        db_membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace.id,
            )
            .first()
        )
        assert db_membership is not None
        assert db_membership.role == OWNER_ROLE

    def test_create_workspace_with_minimal_data(self, db, setup_user, faker):
        """Test creating a workspace with only the required fields."""
        # Arrange
        user = setup_user
        workspace_data = WorkspaceCreate(
            name="Minimal Workspace",
            created_by_id=user.id,
        )

        # Act
        command = CreateWorkspaceCommand(db)
        workspace = command.execute(workspace_data)

        # Assert workspace was created with minimal data
        assert workspace is not None
        assert workspace.name == "Minimal Workspace"
        assert workspace.description is None
        assert workspace.logo is None
        assert workspace.identifier is None
        assert workspace.created_by_id == user.id

        # Assert owner membership was created
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.workspace_id == workspace.id,
            )
            .first()
        )
        assert membership is not None
        assert membership.role == OWNER_ROLE
