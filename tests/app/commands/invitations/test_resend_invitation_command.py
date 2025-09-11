from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.commands.invitations.resend_invitation_command import ResendInvitationCommand
from app.models.invitation import Invitation
from app.constants.membership import MembershipRoles


def test_resend_invitation_command_success(db, setup_invitation):
    """Test ResendInvitationCommand execute method with successful case."""
    original_invitation = setup_invitation
    original_id = original_invitation.id
    original_email = original_invitation.email
    original_workspace_id = original_invitation.workspace_id
    original_role = original_invitation.role
    original_message = original_invitation.message
    original_inviter_id = original_invitation.inviter_id

    command = ResendInvitationCommand(db)
    new_invitation = command.execute(original_id)

    assert new_invitation is not None
    assert new_invitation.id != original_id
    assert new_invitation.email == original_email
    assert new_invitation.workspace_id == original_workspace_id
    assert new_invitation.role == original_role
    assert new_invitation.message == original_message
    assert new_invitation.inviter_id == original_inviter_id

    # Verify the new invitation has a fresh expiration time
    # Ensure timezone-aware comparison
    current_time = datetime.now(timezone.utc)
    if new_invitation.expires_at.tzinfo is None:
        expires_at_aware = new_invitation.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at_aware = new_invitation.expires_at
    assert expires_at_aware > current_time

    # Verify the original invitation was deleted (soft delete)
    from app.services.invitation_service import InvitationService

    invitation_service = InvitationService(db)
    original_after_resend = invitation_service.get_invitation(original_id)
    assert original_after_resend is None


def test_resend_invitation_command_not_found(db):
    """Test ResendInvitationCommand execute method with non-existent invitation."""
    fake_uuid = uuid4()

    command = ResendInvitationCommand(db)
    result = command.execute(fake_uuid)

    assert result is None


def test_resend_invitation_command_with_expired_invitation(
    db, setup_expired_invitation
):
    """Test ResendInvitationCommand execute method with expired invitation."""
    expired_invitation = setup_expired_invitation
    original_id = expired_invitation.id

    command = ResendInvitationCommand(db)
    new_invitation = command.execute(original_id)

    assert new_invitation is not None
    assert new_invitation.id != original_id
    assert new_invitation.email == expired_invitation.email
    assert new_invitation.workspace_id == expired_invitation.workspace_id
    assert new_invitation.role == expired_invitation.role
    assert new_invitation.inviter_id == expired_invitation.inviter_id

    # Verify the new invitation is not expired
    # Ensure timezone-aware comparison
    current_time = datetime.now(timezone.utc)
    if new_invitation.expires_at.tzinfo is None:
        expires_at_aware = new_invitation.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at_aware = new_invitation.expires_at
    assert expires_at_aware > current_time
    assert not new_invitation.is_expired


def test_resend_invitation_command_preserves_all_data(
    db, setup_workspace, setup_user, faker
):
    """Test that ResendInvitationCommand preserves all invitation data including custom fields."""
    # Create invitation with all possible data
    custom_email = faker.email()
    custom_message = faker.text(300)
    custom_role = MembershipRoles.ADMIN

    original_invitation = Invitation(
        email=custom_email,
        workspace_id=setup_workspace.id,
        role=custom_role,
        message=custom_message,
        inviter_id=setup_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(original_invitation)
    db.commit()
    db.refresh(original_invitation)

    command = ResendInvitationCommand(db)
    new_invitation = command.execute(original_invitation.id)

    assert new_invitation is not None
    assert new_invitation.id != original_invitation.id
    assert new_invitation.email == custom_email
    assert new_invitation.workspace_id == setup_workspace.id
    assert new_invitation.role == custom_role
    assert new_invitation.message == custom_message
    assert new_invitation.inviter_id == setup_user.id

    # Verify the new invitation has a fresh expiration time (should be ~24 hours from now)
    # Ensure timezone-aware comparison
    current_time = datetime.now(timezone.utc)
    if new_invitation.expires_at.tzinfo is None:
        expires_at_aware = new_invitation.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at_aware = new_invitation.expires_at
    assert expires_at_aware > current_time
    time_diff = expires_at_aware - current_time
    assert (
        timedelta(hours=23) <= time_diff <= timedelta(hours=25)
    )  # Allow some variance
