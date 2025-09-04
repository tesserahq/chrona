import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.constants.membership import MembershipRoles
from app.models.invitation import Invitation
from app.schemas.invitation import InvitationUpdate
from app.services.invitation_service import InvitationService


class TestGetWorkspaceInvitations:
    """Test GET /workspaces/{workspace_id}/invitations endpoint."""

    def test_get_workspace_invitations_success(
        self, client, setup_workspace, setup_invitation
    ):
        """Test successful retrieval of workspace invitations."""
        workspace = setup_workspace
        invitation = setup_invitation

        response = client.get(f"/workspaces/{workspace.id}/invitations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        invitation_data = data[0]
        assert invitation_data["id"] == str(invitation.id)
        assert invitation_data["email"] == invitation.email
        assert invitation_data["workspace_id"] == str(invitation.workspace_id)
        assert invitation_data["role"] == invitation.role
        assert invitation_data["message"] == invitation.message
        assert invitation_data["inviter_id"] == str(invitation.inviter_id)

    def test_get_workspace_invitations_empty(self, client, setup_workspace):
        """Test getting invitations for workspace with no invitations."""
        workspace = setup_workspace

        response = client.get(f"/workspaces/{workspace.id}/invitations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_workspace_invitations_with_pagination(
        self, client, setup_workspace, setup_multiple_invitations
    ):
        """Test pagination for workspace invitations."""
        workspace = setup_workspace
        invitations = setup_multiple_invitations

        # Test with limit
        response = client.get(f"/workspaces/{workspace.id}/invitations?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

        # Test with skip
        response = client.get(f"/workspaces/{workspace.id}/invitations?skip=2&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

        # Test with skip beyond available data
        response = client.get(f"/workspaces/{workspace.id}/invitations?skip=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 0

    def test_get_workspace_invitations_valid_only_true(
        self, client, setup_workspace, setup_invitation, setup_expired_invitation
    ):
        """Test getting only valid invitations when valid_only=True (default)."""
        workspace = setup_workspace
        valid_invitation = setup_invitation
        expired_invitation = setup_expired_invitation

        response = client.get(f"/workspaces/{workspace.id}/invitations?valid_only=true")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(valid_invitation.id)

    def test_get_workspace_invitations_valid_only_false(
        self, client, setup_workspace, setup_invitation, setup_expired_invitation
    ):
        """Test getting all invitations when valid_only=False."""
        workspace = setup_workspace
        valid_invitation = setup_invitation
        expired_invitation = setup_expired_invitation

        response = client.get(
            f"/workspaces/{workspace.id}/invitations?valid_only=false"
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

        invitation_ids = [inv["id"] for inv in data]
        assert str(valid_invitation.id) in invitation_ids
        assert str(expired_invitation.id) in invitation_ids

    def test_get_workspace_invitations_nonexistent_workspace(self, client):
        """Test getting invitations for non-existent workspace."""
        nonexistent_workspace_id = str(uuid4())

        response = client.get(f"/workspaces/{nonexistent_workspace_id}/invitations")
        assert response.status_code == 404

    def test_get_workspace_invitations_invalid_pagination_params(
        self, client, setup_workspace
    ):
        """Test invalid pagination parameters."""
        workspace = setup_workspace

        # Test negative skip
        response = client.get(f"/workspaces/{workspace.id}/invitations?skip=-1")
        assert response.status_code == 422

        # Test negative limit
        response = client.get(f"/workspaces/{workspace.id}/invitations?limit=-1")
        assert response.status_code == 422

        # Test limit too high
        response = client.get(f"/workspaces/{workspace.id}/invitations?limit=1001")
        assert response.status_code == 422


class TestCreateWorkspaceInvitation:
    """Test POST /workspaces/{workspace_id}/invitations endpoint."""

    def test_create_workspace_invitation_success(
        self, client, setup_workspace, setup_user
    ):
        """Test successful creation of workspace invitation."""
        workspace = setup_workspace
        user = setup_user

        invitation_data = {
            "email": "test@example.com",
            "role": MembershipRoles.COLLABORATOR,
            "message": "Please join our workspace",
        }

        response = client.post(
            f"/workspaces/{workspace.id}/invitations", json=invitation_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == invitation_data["email"]
        assert data["role"] == invitation_data["role"]
        assert data["message"] == invitation_data["message"]
        assert data["workspace_id"] == str(workspace.id)
        assert data["inviter_id"] == str(user.id)
        assert "id" in data
        assert "created_at" in data
        assert "expires_at" in data

    def test_create_workspace_invitation_missing_fields(self, client, setup_workspace):
        """Test creating invitation with missing required fields."""
        workspace = setup_workspace

        # Missing email (required field)
        response = client.post(
            f"/workspaces/{workspace.id}/invitations",
            json={"role": MembershipRoles.COLLABORATOR},
        )
        assert response.status_code == 422

        # Missing role (has default value, should succeed)
        response = client.post(
            f"/workspaces/{workspace.id}/invitations",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 201

    def test_create_workspace_invitation_invalid_email(self, client, setup_workspace):
        """Test creating invitation with invalid email."""
        workspace = setup_workspace

        response = client.post(
            f"/workspaces/{workspace.id}/invitations",
            json={"email": "invalid-email", "role": MembershipRoles.COLLABORATOR},
        )
        assert response.status_code == 422

    def test_create_workspace_invitation_nonexistent_workspace(
        self, client, setup_user
    ):
        """Test creating invitation for non-existent workspace."""
        nonexistent_workspace_id = str(uuid4())

        response = client.post(
            f"/workspaces/{nonexistent_workspace_id}/invitations",
            json={"email": "test@example.com", "role": MembershipRoles.COLLABORATOR},
        )
        assert response.status_code == 404


class TestGetInvitationsByUser:
    """Test GET /invitations endpoint (user's invitations)."""

    def test_get_invitations_by_user_success(
        self, client, setup_invitation_for_current_user
    ):
        """Test successful retrieval of user's invitations."""
        invitation = setup_invitation_for_current_user

        response = client.get("/invitations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        invitation_data = data[0]
        assert invitation_data["id"] == str(invitation.id)
        assert invitation_data["email"] == invitation.email

    def test_get_invitations_by_user_empty(self, client):
        """Test getting invitations when user has none."""
        response = client.get("/invitations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_invitations_by_user_with_pagination(
        self, client, setup_invitation_for_current_user
    ):
        """Test pagination for user invitations."""
        # Create multiple invitations for the current user
        invitation1 = setup_invitation_for_current_user

        response = client.get("/invitations?limit=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        response = client.get("/invitations?skip=1&limit=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 0  # No more invitations after skip=1


class TestGetInvitation:
    """Test GET /invitations/{invitation_id} endpoint."""

    def test_get_invitation_success(self, client, setup_invitation):
        """Test successful retrieval of specific invitation."""
        invitation = setup_invitation

        response = client.get(f"/invitations/{invitation.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(invitation.id)
        assert data["email"] == invitation.email
        assert data["workspace_id"] == str(invitation.workspace_id)
        assert data["role"] == invitation.role
        assert data["message"] == invitation.message

    def test_get_invitation_nonexistent(self, client):
        """Test getting non-existent invitation."""
        nonexistent_invitation_id = str(uuid4())

        response = client.get(f"/invitations/{nonexistent_invitation_id}")
        assert response.status_code == 404


class TestUpdateInvitation:
    """Test PUT /invitations/{invitation_id} endpoint."""

    def test_update_invitation_success(self, client, setup_invitation):
        """Test successful update of invitation."""
        invitation = setup_invitation

        update_data = {
            "message": "Updated invitation message",
            "role": MembershipRoles.ADMIN,
        }

        response = client.put(f"/invitations/{invitation.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == update_data["message"]
        assert data["role"] == update_data["role"]

    def test_update_invitation_nonexistent(self, client):
        """Test updating non-existent invitation."""
        nonexistent_invitation_id = str(uuid4())

        response = client.put(
            f"/invitations/{nonexistent_invitation_id}",
            json={"message": "Updated message"},
        )
        assert response.status_code == 404

    def test_update_invitation_invalid_data(self, client, setup_invitation):
        """Test updating invitation with invalid data."""
        invitation = setup_invitation

        response = client.put(
            f"/invitations/{invitation.id}", json={"role": "invalid-role"}
        )
        assert response.status_code == 422


class TestAcceptInvitation:
    """Test POST /invitations/{invitation_id}/accept endpoint."""

    def test_accept_invitation_success(self, client, setup_invitation_for_current_user):
        """Test successful acceptance of invitation."""
        invitation = setup_invitation_for_current_user

        response = client.post(f"/invitations/{invitation.id}/accept")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Invitation accepted successfully"
        assert "membership_id" in data

    def test_accept_invitation_nonexistent(self, client):
        """Test accepting non-existent invitation."""
        nonexistent_invitation_id = str(uuid4())

        response = client.post(f"/invitations/{nonexistent_invitation_id}/accept")
        assert response.status_code == 404

    def test_accept_invitation_wrong_email(
        self, db, client, setup_invitation_for_wrong_email
    ):
        """Test accepting invitation with wrong email."""
        invitation = setup_invitation_for_wrong_email

        response = client.post(f"/invitations/{invitation.id}/accept")
        assert response.status_code == 400

    def test_accept_invitation_expired(self, client, setup_expired_invitation):
        """Test accepting expired invitation."""
        invitation = setup_expired_invitation

        response = client.post(f"/invitations/{invitation.id}/accept")
        assert response.status_code == 400


class TestDeclineInvitation:
    """Test POST /invitations/{invitation_id}/decline endpoint."""

    def test_decline_invitation_success(
        self, client, setup_invitation_for_current_user
    ):
        """Test successful decline of invitation."""
        invitation = setup_invitation_for_current_user

        response = client.post(f"/invitations/{invitation.id}/decline")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Invitation declined successfully"

    def test_decline_invitation_nonexistent(self, client):
        """Test declining non-existent invitation."""
        nonexistent_invitation_id = str(uuid4())

        response = client.post(f"/invitations/{nonexistent_invitation_id}/decline")
        assert response.status_code == 404

    def test_decline_invitation_wrong_email(self, client, setup_invitation):
        """Test declining invitation with wrong email."""
        invitation = setup_invitation

        response = client.post(f"/invitations/{invitation.id}/decline")
        assert response.status_code == 400


class TestDeleteInvitation:
    """Test DELETE /invitations/{invitation_id} endpoint."""

    def test_delete_invitation_success(self, client, setup_invitation):
        """Test successful deletion of invitation."""
        invitation = setup_invitation

        response = client.delete(f"/invitations/{invitation.id}")
        assert response.status_code == 204

    def test_delete_invitation_nonexistent(self, client):
        """Test deleting non-existent invitation."""
        nonexistent_invitation_id = str(uuid4())

        response = client.delete(f"/invitations/{nonexistent_invitation_id}")
        assert response.status_code == 404


class TestCleanupExpiredInvitations:
    """Test POST /invitations/cleanup endpoint."""

    def test_cleanup_expired_invitations_success(
        self, client, setup_expired_invitation
    ):
        """Test successful cleanup of expired invitations."""
        expired_invitation = setup_expired_invitation

        response = client.post("/invitations/cleanup")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Cleaned up 1 expired invitations"
        assert data["deleted_count"] == 1

    def test_cleanup_expired_invitations_no_expired(self, client):
        """Test cleanup when no expired invitations exist."""
        response = client.post("/invitations/cleanup")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Cleaned up 0 expired invitations"
        assert data["deleted_count"] == 0


class TestGetPendingInvitationsCount:
    """Test GET /workspaces/{workspace_id}/invitations/count endpoint."""

    def test_get_pending_invitations_count_success(
        self, client, setup_workspace, setup_invitation
    ):
        """Test successful retrieval of pending invitations count."""
        workspace = setup_workspace
        invitation = setup_invitation

        response = client.get(f"/workspaces/{workspace.id}/invitations/count")
        assert response.status_code == 200

        data = response.json()
        assert data["pending_invitations_count"] == 1

    def test_get_pending_invitations_count_empty(self, client, setup_workspace):
        """Test getting count when no pending invitations exist."""
        workspace = setup_workspace

        response = client.get(f"/workspaces/{workspace.id}/invitations/count")
        assert response.status_code == 200

        data = response.json()
        assert data["pending_invitations_count"] == 0

    def test_get_pending_invitations_count_nonexistent_workspace(self, client):
        """Test getting count for non-existent workspace."""
        nonexistent_workspace_id = str(uuid4())

        response = client.get(
            f"/workspaces/{nonexistent_workspace_id}/invitations/count"
        )
        assert response.status_code == 404
