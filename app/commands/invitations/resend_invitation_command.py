from typing import Optional
from uuid import UUID
from typing import cast, Optional as _Optional
from sqlalchemy.orm import Session

from app.services.invitation_service import InvitationService
from app.models.invitation import Invitation
from app.schemas.invitation import InvitationCreate


class ResendInvitationCommand:
    """
    Command to resend an invitation by deleting the existing one and creating a new one.
    """

    def __init__(self, db: Session):
        self.db = db
        self.invitation_service = InvitationService(db)

    def execute(self, invitation_id: UUID) -> Optional[Invitation]:
        """
        Execute the command to resend an invitation.

        Args:
            invitation_id: The ID of the invitation to resend

        Returns:
            Invitation: The newly created invitation, or None if original invitation not found

        Raises:
            Exception: If resending fails
        """
        try:
            # Get the original invitation
            original_invitation = self.invitation_service.get_invitation(invitation_id)

            if not original_invitation:
                return None

            # Store the original invitation data
            invitation_data = InvitationCreate(
                email=cast(str, original_invitation.email),
                workspace_id=cast(UUID, original_invitation.workspace_id),
                role=cast(str, original_invitation.role),
                message=cast(_Optional[str], original_invitation.message),
                inviter_id=cast(UUID, original_invitation.inviter_id),
                projects=getattr(original_invitation, "projects", None),
            )

            # Delete the existing invitation
            self.invitation_service.delete_invitation(invitation_id)

            # Create a new invitation with the same data
            new_invitation = self.invitation_service.create_invitation(invitation_data)

            return new_invitation

        except Exception as e:
            # Rollback the transaction if something goes wrong
            self.db.rollback()
            raise Exception(f"Failed to resend invitation: {str(e)}")
