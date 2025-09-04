import pytest
from datetime import datetime, timedelta, timezone

from app.models.invitation import Invitation
from app.constants.membership import MembershipRoles


@pytest.fixture
def setup_invitation(db, setup_workspace, setup_user, faker):
    """Create a basic invitation fixture."""
    invitation = Invitation(
        email=faker.email(),
        workspace_id=setup_workspace.id,
        role=MembershipRoles.COLLABORATOR,
        message=faker.text(100),
        inviter_id=setup_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


@pytest.fixture
def setup_expired_invitation(db, setup_workspace, setup_user, faker):
    """Create an expired invitation fixture."""
    invitation = Invitation(
        email=faker.email(),
        workspace_id=setup_workspace.id,
        role=MembershipRoles.COLLABORATOR,
        message=faker.text(100),
        inviter_id=setup_user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


@pytest.fixture
def setup_multiple_invitations(db, setup_workspace, setup_user, faker):
    """Create multiple invitations for testing pagination and filtering."""
    invitations = []
    for i in range(5):
        invitation = Invitation(
            email=faker.email(),
            workspace_id=setup_workspace.id,
            role=MembershipRoles.COLLABORATOR,
            message=faker.text(100),
            inviter_id=setup_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(invitation)
        invitations.append(invitation)

    db.commit()
    for invitation in invitations:
        db.refresh(invitation)

    return invitations


@pytest.fixture
def setup_invitation_for_user_email(
    db, setup_workspace, setup_user, setup_another_user, faker
):
    """Create an invitation for a specific user's email."""
    invitation = Invitation(
        email=setup_another_user.email,
        workspace_id=setup_workspace.id,
        role=MembershipRoles.COLLABORATOR,
        message=faker.text(100),
        inviter_id=setup_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


@pytest.fixture
def setup_invitation_for_current_user(
    db, setup_workspace, setup_user, setup_another_user, faker
):
    """Create an invitation for a specific user's email."""
    user = setup_user
    account = setup_workspace
    another_user = setup_another_user
    invitation = Invitation(
        email=user.email,
        workspace_id=account.id,
        role=MembershipRoles.COLLABORATOR,
        message=faker.text(100),
        inviter_id=another_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


@pytest.fixture
def setup_invitation_for_wrong_email(db, setup_invitation):
    """Create an invitation for a wrong email."""
    invitation = setup_invitation
    invitation.email = "wrong@example.com"
    db.commit()
    db.refresh(invitation)
    return invitation
