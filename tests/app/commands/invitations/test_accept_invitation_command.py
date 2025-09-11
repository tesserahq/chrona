import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.commands.invitations.accept_invitation_command import AcceptInvitationCommand
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.models.project_membership import ProjectMembership
from app.constants.membership import MembershipRoles
from app.services.invitation_service import InvitationService
from app.exceptions.invitation_exceptions import (
    InvitationExpiredError,
    InvitationNotFoundError,
)


class TestAcceptInvitationCommand:
    """Test cases for AcceptInvitationCommand."""

    def test_accept_invitation_success(
        self,
        db,
        setup_workspace,
        setup_user,
        setup_invitation_for_current_user,
        setup_invitation,
    ):
        """Test successfully accepting an invitation and creating a membership."""
        invitation = setup_invitation_for_current_user
        accepting_user = setup_user

        # Execute command
        command = AcceptInvitationCommand(db)
        membership = command.execute(invitation.id, accepting_user.id)

        # Verify membership was created
        assert membership is not None
        assert membership.user_id == accepting_user.id
        assert membership.workspace_id == setup_workspace.id
        assert membership.role == MembershipRoles.COLLABORATOR
        assert membership.created_by_id == invitation.inviter_id

        # Verify invitation was deleted
        deleted_invitation = InvitationService(db).get_invitation(invitation.id)
        assert deleted_invitation is None

    def test_accept_invitation_not_found(self, db, setup_user):
        """Test accepting a non-existent invitation."""
        accepting_user = setup_user
        non_existent_id = uuid4()

        command = AcceptInvitationCommand(db)

        with pytest.raises(
            InvitationNotFoundError,
            match=f"Invitation with ID {non_existent_id} not found",
        ):
            command.execute(non_existent_id, accepting_user.id)

    def test_accept_expired_invitation(self, db, setup_workspace, setup_user, faker):
        """Test accepting an expired invitation."""
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

        # Create user who will try to accept the invitation
        accepting_user = setup_user
        accepting_user.email = "test@example.com"
        db.commit()

        # Execute command
        command = AcceptInvitationCommand(db)

        with pytest.raises(InvitationExpiredError, match="Invitation has expired"):
            command.execute(invitation.id, accepting_user.id)

        # Verify invitation still exists (not deleted)
        existing_invitation = (
            db.query(Invitation).filter(Invitation.id == invitation.id).first()
        )
        assert existing_invitation is not None

        # Verify no membership was created
        memberships = (
            db.query(Membership)
            .filter(
                Membership.user_id == accepting_user.id,
                Membership.workspace_id == setup_workspace.id,
            )
            .all()
        )
        assert len(memberships) == 1
        assert memberships[0].role == MembershipRoles.OWNER

    def test_accept_invitation_different_role(
        self, db, setup_workspace, setup_user, faker
    ):
        """Test accepting an invitation with a different membership type."""
        # Create inviter user
        inviter = setup_user

        # Create invitation with OWNER membership type
        invitation = Invitation(
            id=uuid4(),
            email="test@example.com",
            workspace_id=setup_workspace.id,
            inviter_id=inviter.id,
            role=MembershipRoles.OWNER,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            message="Test invitation",
        )
        db.add(invitation)
        db.commit()

        # Create user who will accept the invitation
        accepting_user = setup_user
        accepting_user.email = "test@example.com"
        db.commit()

        # Execute command
        command = AcceptInvitationCommand(db)
        membership = command.execute(invitation.id, accepting_user.id)

        # Verify membership was created with correct type
        assert membership is not None
        assert membership.role == MembershipRoles.OWNER
        assert membership.user_id == accepting_user.id
        assert membership.workspace_id == setup_workspace.id

    def test_accept_project_invitation_creates_project_memberships_and_workspace_project_member(
        self, db, setup_workspace, setup_user, setup_another_user, setup_project, faker
    ):
        """Accepting an invitation with projects creates project memberships and sets workspace role to project_member."""
        workspace = setup_workspace
        inviter = setup_another_user
        accepting_user = setup_user

        # Ensure accepting_user email matches invitation
        accepting_user.email = "project-invitee@example.com"
        db.commit()

        # Create two projects in the same workspace
        project1 = setup_project
        # Create another project
        from app.models.project import Project as ProjectModel

        project2 = ProjectModel(
            name=faker.company(), description=faker.text(50), workspace_id=workspace.id
        )
        db.add(project2)
        db.commit()
        db.refresh(project2)

        # Create invitation with projects assignments
        invitation = Invitation(
            email=accepting_user.email,
            workspace_id=workspace.id,
            inviter_id=inviter.id,
            role=MembershipRoles.COLLABORATOR,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            message="Project-specific invitation",
            projects=[
                {"id": project1.id, "role": "admin"},
                {"id": project2.id, "role": "collaborator"},
            ],
        )
        db.add(invitation)
        db.commit()

        # Execute command
        command = AcceptInvitationCommand(db)
        membership = command.execute(invitation.id, accepting_user.id)

        # Verify workspace membership exists with project_member role
        assert membership is not None
        assert membership.role == MembershipRoles.PROJECT_MEMBER
        assert membership.user_id == accepting_user.id
        assert membership.workspace_id == workspace.id

        # Verify project memberships created for accepting_user
        pmemberships = (
            db.query(ProjectMembership)
            .filter(ProjectMembership.user_id == accepting_user.id)
            .all()
        )
        assert len(pmemberships) == 2
        mapped = {str(pm.project_id): pm for pm in pmemberships}
        assert str(project1.id) in mapped and mapped[str(project1.id)].role == "admin"
        assert (
            str(project2.id) in mapped
            and mapped[str(project2.id)].role == "collaborator"
        )

        # Invitation should be deleted
        assert InvitationService(db).get_invitation(invitation.id) is None

    def test_accept_project_invitation_missing_role_defaults_to_collaborator(
        self, db, setup_workspace, setup_user, setup_another_user, setup_project, faker
    ):
        """If a project assignment lacks a role, default to collaborator for that project membership."""
        workspace = setup_workspace
        inviter = setup_another_user
        accepting_user = setup_user
        accepting_user.email = "project-invitee2@example.com"
        db.commit()

        project = setup_project

        # Create invitation with one project assignment without role
        invitation = Invitation(
            email=accepting_user.email,
            workspace_id=workspace.id,
            inviter_id=inviter.id,
            role=MembershipRoles.COLLABORATOR,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            message="Project invite without role",
            projects=[{"id": project.id}],
        )
        db.add(invitation)
        db.commit()

        command = AcceptInvitationCommand(db)
        membership = command.execute(invitation.id, accepting_user.id)

        # Workspace membership should be project_member
        assert membership is not None
        assert membership.role == MembershipRoles.PROJECT_MEMBER

        # Project membership defaults to collaborator
        pm = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.user_id == accepting_user.id,
                ProjectMembership.project_id == project.id,
            )
            .first()
        )
        assert pm is not None
        assert pm.role == "collaborator"
