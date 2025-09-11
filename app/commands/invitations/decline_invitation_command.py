from uuid import UUID
from sqlalchemy.orm import Session

from app.services.invitation_service import InvitationService
from app.exceptions.invitation_exceptions import (
    InvitationException,
)


class DeclineInvitationCommand:
    """
    Command to decline an invitation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.invitation_service = InvitationService(db)

    def execute(self, invitation_id: UUID, invited_user_email: str) -> bool:
        """
        Execute the command to decline an invitation.

        Args:
            invitation_id: The ID of the invitation to decline
            user_email: The email of the user declining the invitation

        Returns:
            bool: True if invitation was successfully declined

        Raises:
            InvitationException: If invitation decline fails
        """
        try:
            # Decline the invitation
            success = self.invitation_service.decline_invitation(
                invitation_id, invited_user_email
            )

            return success

        except InvitationException as e:
            # Re-raise invitation-specific exceptions without rollback
            raise e
        except Exception as e:
            # Rollback the transaction if something goes wrong
            self.db.rollback()
            raise Exception(f"Failed to decline invitation: {str(e)}")
