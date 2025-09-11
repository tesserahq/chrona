import uuid
from app.config import get_settings
from app.ext.quore_service import QuoreService
from app.schemas.membership import MembershipCreate
from app.schemas.workspace import Workspace, WorkspaceCreate, WorkspaceUpdate
from app.services.membership_service import MembershipService
from app.services.workspace_service import WorkspaceService
from sqlalchemy.orm import Session
from uuid import UUID
from app.constants.membership import OWNER_ROLE
from app.utils.m2m_token import M2MTokenClient


class CreateWorkspaceCommand:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.workspace_service = WorkspaceService(db)
        self.membership_service = MembershipService(db)

    def execute(self, workspace_create: WorkspaceCreate) -> Workspace:
        """
        Execute the command to create a new workspace.

        :param workspace_create: The data required to create a new workspace.
        :return: The created Workspace object.
        """
        workspace = self.workspace_service.create_workspace(workspace_create)

        # Create an owner membership for the user who created the workspace
        self._create_owner_membership(workspace, workspace.created_by_id)

        return workspace

    def _create_owner_membership(self, workspace: Workspace, user_id: UUID):
        """
        Create an owner membership for the user in the specified workspace.

        :param workspace_id: The ID of the workspace.
        :param user_id: The ID of the user to be added as an owner.
        """
        membership_data = MembershipCreate(
            user_id=user_id,
            workspace_id=workspace.id,
            role=OWNER_ROLE,
            created_by_id=workspace.created_by_id,
        )
        self.membership_service.create_membership(membership_data)
