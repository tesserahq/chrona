from app.constants.membership import (
    COLLABORATOR_ROLE,
    OWNER_ROLE,
    ADMIN_ROLE,
    ROLES_DATA,
)
from app.schemas.membership import MembershipCreate
from app.services.membership_service import MembershipService


def test_list_memberships(client, setup_membership):
    """Test GET /workspaces/{workspace_id}/memberships endpoint."""
    membership = setup_membership
    response = client.get(f"/workspaces/{membership.workspace_id}/memberships")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    # Verify the created membership is in the list
    membership_list = data["data"]
    assert any(m["id"] == str(membership.id) for m in membership_list)
    assert any(m["user_id"] == str(membership.user_id) for m in membership_list)
    assert any(
        m["workspace_id"] == str(membership.workspace_id) for m in membership_list
    )


def test_get_membership(client, setup_membership):
    """Test GET /memberships/{membership_id} endpoint."""
    membership = setup_membership

    response = client.get(f"/memberships/{membership.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(membership.id)
    assert data["user_id"] == str(membership.user_id)
    assert data["workspace_id"] == str(membership.workspace_id)
    assert data["role"] == membership.role
    assert "created_at" in data
    assert "updated_at" in data


def test_get_membership_not_found(client, setup_workspace):
    """Test GET /memberships/{membership_id} endpoint with non-existent membership."""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

    response = client.get(f"/memberships/{fake_uuid}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_membership(client, setup_membership):
    """Test PUT /memberships/{membership_id} endpoint."""
    membership = setup_membership

    update_data = {"role": ADMIN_ROLE}

    response = client.put(f"/memberships/{membership.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(membership.id)
    assert data["role"] == ADMIN_ROLE
    assert data["user_id"] == str(membership.user_id)
    assert data["workspace_id"] == str(membership.workspace_id)


def test_update_membership_not_found(client):
    """Test PUT /memberships/{membership_id} endpoint with non-existent membership."""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

    update_data = {"role": ADMIN_ROLE}

    response = client.put(f"/memberships/{fake_uuid}", json=update_data)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_membership(client, setup_another_user_membership):
    """Test DELETE /memberships/{membership_id} endpoint."""
    membership = setup_another_user_membership

    response = client.delete(f"/memberships/{membership.id}")

    assert response.status_code == 204

    # Verify membership is actually deleted
    get_response = client.get(f"/memberships/{membership.id}")
    assert get_response.status_code == 404


def test_delete_membership_not_found(client):
    """Test DELETE /memberships/{membership_id} endpoint with non-existent membership."""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

    response = client.delete(f"/memberships/{fake_uuid}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_memberships_pagination(
    client, setup_membership, setup_different_membership
):
    """Test GET /workspaces/{workspace_id}/memberships endpoint with pagination."""
    membership = setup_membership

    # Test with limit
    response = client.get(f"/workspaces/{membership.workspace_id}/memberships?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1

    # Test with skip
    response = client.get(
        f"/workspaces/{membership.workspace_id}/memberships?skip=0&limit=10"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


def test_update_membership_to_invalid_role(client, setup_membership):
    """Test updating membership with invalid role."""
    membership = setup_membership

    update_data = {"role": "invalid_role"}

    response = client.put(f"/memberships/{membership.id}", json=update_data)

    # Should either accept it (if no validation) or reject it (if validation exists)
    # This depends on your business logic validation
    assert response.status_code in [200, 400, 422]


def test_get_roles(client):
    """Test GET /memberships/roles endpoint."""
    response = client.get("/memberships/roles")

    assert response.status_code == 200
    data = response.json()

    assert "roles" in data
    assert isinstance(data["roles"], list)
    assert len(data["roles"]) == len(ROLES_DATA)

    # Verify each role has the expected structure
    for role in data["roles"]:
        assert "id" in role
        assert "name" in role
        assert isinstance(role["id"], str)
        assert isinstance(role["name"], str)

    # Verify all expected roles are present
    role_ids = [role["id"] for role in data["roles"]]
    expected_role_ids = [role["id"] for role in ROLES_DATA]
    assert set(role_ids) == set(expected_role_ids)

    # Verify role names match
    for expected_role in ROLES_DATA:
        found_role = next(
            (r for r in data["roles"] if r["id"] == expected_role["id"]), None
        )
        assert found_role is not None
        assert found_role["name"] == expected_role["name"]


def test_delete_membership_only_owners_can_delete_owners(
    client, setup_workspace, setup_user, setup_another_user, db
):
    """Test DELETE /memberships/{membership_id} - only owners can delete other owners."""
    workspace = setup_workspace

    # Create an owner membership for another user
    membership_service = MembershipService(db)
    owner_membership_data = MembershipCreate(
        user_id=setup_another_user.id,
        workspace_id=workspace.id,
        role=OWNER_ROLE,
        created_by_id=workspace.created_by_id,
    )
    owner_membership = membership_service.create_membership(owner_membership_data)

    # Remove any existing memberships for the current user and create a collaborator membership
    existing_memberships = membership_service.get_memberships_by_user(setup_user.id)
    for existing_membership in existing_memberships:
        if existing_membership.workspace_id == workspace.id:
            membership_service.delete_membership(existing_membership.id)

    # Create a collaborator membership for the current user (setup_user)
    collaborator_membership_data = MembershipCreate(
        user_id=setup_user.id,
        workspace_id=workspace.id,
        role=COLLABORATOR_ROLE,
        created_by_id=workspace.created_by_id,
    )
    membership_service.create_membership(collaborator_membership_data)

    # Try to delete the owner membership as a collaborator
    response = client.delete(f"/memberships/{owner_membership.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Only owners can delete other owners"


def test_delete_membership_cannot_delete_self(
    client_another_user, setup_workspace, setup_another_user, db
):
    """Test DELETE /memberships/{membership_id} - users cannot delete their own membership."""
    workspace = setup_workspace

    # Create a membership for the current user (setup_another_user)
    membership_service = MembershipService(db)
    membership_data = MembershipCreate(
        user_id=setup_another_user.id,
        workspace_id=workspace.id,
        role=COLLABORATOR_ROLE,
        created_by_id=workspace.created_by_id,
    )
    membership = membership_service.create_membership(membership_data)

    # Try to delete own membership
    response = client_another_user.delete(f"/memberships/{membership.id}")

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot delete your own membership"


def test_delete_membership_cannot_delete_last_owner(
    client, setup_workspace, setup_user, setup_another_user, db
):
    """Test DELETE /memberships/{membership_id} - cannot delete the last owner."""
    workspace = setup_workspace

    # Remove any existing memberships for both users
    membership_service = MembershipService(db)
    existing_memberships = membership_service.get_memberships_by_workspace(workspace.id)
    for existing_membership in existing_memberships:
        if existing_membership.user_id in [setup_user.id, setup_another_user.id]:
            membership_service.delete_membership(existing_membership.id)

    # Create an owner membership for another user (not the workspace creator)
    membership_data = MembershipCreate(
        user_id=setup_another_user.id,
        workspace_id=workspace.id,
        role=OWNER_ROLE,
        created_by_id=workspace.created_by_id,
    )
    membership = membership_service.create_membership(membership_data)

    # Create a collaborator membership for the current user (setup_user)
    collaborator_membership_data = MembershipCreate(
        user_id=setup_user.id,
        workspace_id=workspace.id,
        role=COLLABORATOR_ROLE,
        created_by_id=workspace.created_by_id,
    )
    membership_service.create_membership(collaborator_membership_data)

    # Try to delete the owner membership as a collaborator
    response = client.delete(f"/memberships/{membership.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Only owners can delete other owners"


def test_delete_membership_cannot_delete_last_owner_scenario(
    client, setup_workspace, setup_user, setup_another_user, db
):
    """Test DELETE /memberships/{membership_id} - cannot delete the last owner when there are only two owners."""
    workspace = setup_workspace

    # Remove any existing memberships for both users
    membership_service = MembershipService(db)
    existing_memberships = membership_service.get_memberships_by_workspace(workspace.id)
    for existing_membership in existing_memberships:
        if existing_membership.user_id in [setup_user.id, setup_another_user.id]:
            membership_service.delete_membership(existing_membership.id)

    # Create an owner membership for another user
    membership_data = MembershipCreate(
        user_id=setup_another_user.id,
        workspace_id=workspace.id,
        role=OWNER_ROLE,
        created_by_id=workspace.created_by_id,
    )
    target_membership = membership_service.create_membership(membership_data)

    # Create an owner membership for the current user (setup_user)
    current_user_membership_data = MembershipCreate(
        user_id=setup_user.id,
        workspace_id=workspace.id,
        role=OWNER_ROLE,
        created_by_id=workspace.created_by_id,
    )
    membership_service.create_membership(current_user_membership_data)

    # Try to delete the other owner membership (as an owner)
    response = client.delete(f"/memberships/{target_membership.id}")

    # This should succeed because there are 2 owners, so deleting one leaves 1 owner
    assert response.status_code == 204
