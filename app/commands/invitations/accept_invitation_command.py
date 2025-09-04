from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.services.invitation_service import InvitationService
from app.services.membership_service import MembershipService
from app.models.membership import Membership
from app.schemas.membership import MembershipCreate
from app.services.user_service import UserService
from app.services.project_membership_service import ProjectMembershipService
from app.schemas.project_membership import ProjectMembershipCreate
from app.exceptions.invitation_exceptions import (
    InvitationException,
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationUnauthorizedError,
    UserNotFoundError,
)
from app.constants.membership import MembershipRoles


class AcceptInvitationCommand:
    """
    Command to accept an invitation and create a membership for the user.
    """

    def __init__(self, db: Session):
        self.db = db
        self.invitation_service = InvitationService(db)
        self.membership_service = MembershipService(db)
        self.user_service = UserService(db)
        self.project_membership_service = ProjectMembershipService(db)

    def execute(
        self, invitation_id: UUID, accepted_by_id: UUID
    ) -> Optional[Membership]:
        """
        Execute the command to accept an invitation and create a membership.

        Args:
            invitation_id: The ID of the invitation to accept
            accepted_by_id: The ID of the user accepting the invitation

        Returns:
            Membership: The created membership, or None if invitation not found

        Raises:
            ValueError: If invitation has expired
            Exception: If invitation acceptance fails
        """
        try:
            user = self.user_service.get_user(accepted_by_id)
            if not user:
                raise UserNotFoundError(f"User with ID {accepted_by_id} not found")

            invitation = self.invitation_service.get_invitation(invitation_id)
            if not invitation:
                raise InvitationNotFoundError(
                    f"Invitation with ID {invitation_id} not found"
                )

            if invitation.email != user.email:
                raise InvitationUnauthorizedError(
                    "You are not authorized to accept this invitation."
                )

            # Store invitation data before accepting (which will delete it)
            workspace_id = UUID(str(invitation.workspace_id))
            role = str(invitation.role)
            inviter_id = UUID(str(invitation.inviter_id))

            # Accept the invitation
            accepted_invitation = self.invitation_service.accept_invitation(
                invitation_id
            )

            # Determine workspace role: if this is a "project invitation", use Project member; otherwise use requested role
            project_assignments = getattr(invitation, "projects", None) or []
            workspace_role = (
                MembershipRoles.PROJECT_MEMBER if project_assignments else role
            )

            # Create workspace membership
            membership_data = MembershipCreate(
                user_id=accepted_by_id,
                workspace_id=workspace_id,
                role=workspace_role,
                created_by_id=inviter_id,
            )

            membership = self.membership_service.create_membership(membership_data)

            # If the invitation includes project assignments, create project memberships too
            for assignment in project_assignments:
                pm_data = ProjectMembershipCreate(
                    user_id=accepted_by_id,
                    project_id=assignment.get("id"),
                    role=assignment.get("role", MembershipRoles.COLLABORATOR),
                    created_by_id=inviter_id,
                )
                self.project_membership_service.create_project_membership(pm_data)

            return membership

        except InvitationException as e:
            # Re-raise invitation-specific exceptions without rollback
            raise e
        except Exception as e:
            # Rollback the transaction if something goes wrong
            self.db.rollback()
            raise Exception(f"Failed to accept invitation: {str(e)}")
