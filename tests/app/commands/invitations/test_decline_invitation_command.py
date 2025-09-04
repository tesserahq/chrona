import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.commands.invitations.decline_invitation_command import DeclineInvitationCommand
from app.models.invitation import Invitation
from app.constants.membership import MembershipRoles
from app.exceptions.invitation_exceptions import (
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationUnauthorizedError,
)
from app.services.invitation_service import InvitationService


class TestDeclineInvitationCommand:
    """Test cases for DeclineInvitationCommand."""

    def test_decline_invitation_success(self, db, setup_invitation):
        """Test successfully declining an invitation."""
        invitation = setup_invitation

        # Execute command
        command = DeclineInvitationCommand(db)
        success = command.execute(invitation.id, invitation.email)

        # Verify invitation was declined
        assert success is True

        # Verify invitation was deleted
        deleted_invitation = InvitationService(db).get_invitation(invitation.id)
        assert deleted_invitation is None

    def test_decline_invitation_not_found(self, db, faker):
        """Test declining a non-existent invitation."""
        non_existent_id = uuid4()

        command = DeclineInvitationCommand(db)

        with pytest.raises(
            InvitationNotFoundError,
            match=f"Invitation with ID {non_existent_id} not found",
        ):
            command.execute(non_existent_id, "test@example.com")

    def test_decline_expired_invitation(self, db, setup_workspace, setup_user, faker):
        """Test declining an expired invitation."""
        # Create inviter user
        inviter = setup_user

        # Create expired invitation
        invitation = Invitation(
            id=uuid4(),
            email="test@example.com",
            workspace_id=setup_workspace.id,
            inviter_id=inviter.id,
            role=MembershipRoles.COLLABORATOR,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            message="Test invitation",
        )
        db.add(invitation)
        db.commit()

        # Execute command
        command = DeclineInvitationCommand(db)

        with pytest.raises(InvitationExpiredError, match="Invitation has expired"):
            command.execute(invitation.id, "test@example.com")

        # Verify invitation still exists (not deleted)
        existing_invitation = (
            db.query(Invitation).filter(Invitation.id == invitation.id).first()
        )
        assert existing_invitation is not None

    def test_decline_invitation_wrong_user(
        self, db, setup_workspace, setup_user, faker
    ):
        """Test declining an invitation with wrong user email."""
        # Create inviter user
        inviter = setup_user

        # Create invitation
        invitation = Invitation(
            id=uuid4(),
            email="test@example.com",
            workspace_id=setup_workspace.id,
            inviter_id=inviter.id,
            role=MembershipRoles.COLLABORATOR,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            message="Test invitation",
        )
        db.add(invitation)
        db.commit()

        # Execute command with wrong email
        command = DeclineInvitationCommand(db)

        with pytest.raises(
            InvitationUnauthorizedError,
            match="Only the invited user can decline this invitation",
        ):
            command.execute(invitation.id, "wrong@email.com")

        # Verify invitation still exists (not deleted)
        existing_invitation = (
            db.query(Invitation).filter(Invitation.id == invitation.id).first()
        )
        assert existing_invitation is not None
