from app.config import get_settings
from app.ext.quore_service import QuoreService
from app.schemas.project_membership import ProjectMembershipCreate
from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.services.project_membership_service import ProjectMembershipService
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService
from sqlalchemy.orm import Session
from uuid import UUID
from app.constants.membership import PROJECT_MEMBER_ROLE
from app.utils.m2m_token import M2MTokenClient


class CreateProjectCommand:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.project_service = ProjectService(db)
        self.project_membership_service = ProjectMembershipService(db)
        self.workspace_service = WorkspaceService(db)

    def execute(self, project_create: ProjectCreate, created_by_id: UUID) -> Project:
        """
        Execute the command to create a new project.

        :param project_create: The data required to create a new project.
        :param created_by_id: The ID of the user creating the project.
        :return: The created Project object.
        """
        # Validate workspace exists
        if not project_create.workspace_id:
            raise ValueError("Workspace ID is required to create a project")

        workspace = self.workspace_service.get_workspace(project_create.workspace_id)
        if not workspace:
            raise ValueError(
                f"Workspace with ID {project_create.workspace_id} not found"
            )

        # Create the project
        project = self.project_service.create_project(project_create)

        # Create a project membership for the user who created the project
        self._create_project_membership(project, created_by_id)

        # Create project in Quore
        self._create_quore_project(project, workspace)

        return project

    def _create_project_membership(self, project: Project, user_id: UUID):
        """
        Create a project membership for the user in the specified project.

        :param project: The project object.
        :param user_id: The ID of the user to be added as a project member.
        """
        membership_data = ProjectMembershipCreate(
            user_id=user_id,
            project_id=project.id,
            role=PROJECT_MEMBER_ROLE,
            created_by_id=user_id,
        )
        self.project_membership_service.create_project_membership(membership_data)

    def _create_quore_project(self, project: Project, workspace):
        """
        Create a new project in Quore.

        :param project: The project to create.
        :param workspace: The workspace the project belongs to.
        """

        if not get_settings().quore_enabled:
            return

        if not workspace.quore_workspace_id:
            # Skip Quore project creation if workspace doesn't have a Quore ID
            return

        quore_service = QuoreService()
        m2m_token = self._get_m2m_token()

        # Use project labels or create default ones
        labels = project.labels or {}

        quore_project = quore_service.create_project(
            project.name, labels, workspace.quore_workspace_id, m2m_token
        )
        project.quore_project_id = quore_project["id"]

        # Update the project with the Quore ID
        self.project_service.update_project(
            project.id, ProjectUpdate(quore_project_id=quore_project["id"])
        )

    def _get_m2m_token(self) -> str:
        """
        Get an M2M token for Quore.
        """
        return M2MTokenClient().get_token_sync().access_token
