from typing import List
from app.utils.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.utils.dependencies import (
    get_workspace_by_id,
    get_invitation_by_id,
)
from app.schemas.invitation import (
    InvitationCreate,
    InvitationUpdate,
    InvitationCreateRequest,
    InvitationResponse,
)
from app.models.invitation import Invitation
from app.services.invitation_service import InvitationService
from app.models.workspace import Workspace
from app.models.user import User

router = APIRouter(
    tags=["invitations"],
    responses={404: {"description": "Not found"}},
)


# Workspace-based invitation endpoints
@router.get(
    "/workspaces/{workspace_id}/invitations", response_model=List[InvitationResponse]
)
def get_workspace_invitations(
    workspace: Workspace = Depends(get_workspace_by_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    valid_only: bool = Query(
        True, description="Only return valid (unexpired, unaccepted) invitations"
    ),
    db: Session = Depends(get_db),
):
    """Get all invitations for a specific workspace with pagination."""
    invitation_service = InvitationService(db)
    invitations = invitation_service.get_invitations_by_workspace(
        workspace.id, skip=skip, limit=limit, valid_only=valid_only
    )
    return invitations


@router.post(
    "/workspaces/{workspace_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace_invitation(
    invitation_data: InvitationCreateRequest,
    workspace: Workspace = Depends(get_workspace_by_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new invitation for a specific workspace."""
    invitation_service = InvitationService(db)

    # Convert InvitationCreateRequest to InvitationCreate by adding workspace_id
    invitation_create_data = invitation_data.model_dump()
    invitation_create_data["workspace_id"] = workspace.id
    invitation_create_data["inviter_id"] = current_user.id
    invitation_create = InvitationCreate(**invitation_create_data)

    invitation = invitation_service.create_invitation(invitation_create)
    return invitation


@router.get("/invitations", response_model=List[InvitationResponse])
def get_invitations_by_user(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all valid invitations for the current user."""
    invitation_service = InvitationService(db)
    invitations = invitation_service.get_invitations_by_email(
        current_user.email, skip=skip, limit=limit, valid_only=True
    )
    return invitations


# Individual invitation endpoints
@router.get("/invitations/{invitation_id}", response_model=InvitationResponse)
def get_invitation(
    invitation: Invitation = Depends(get_invitation_by_id),
):
    """Get a specific invitation by ID."""
    return invitation


@router.put("/invitations/{invitation_id}", response_model=InvitationResponse)
def update_invitation(
    invitation_data: InvitationUpdate,
    invitation: Invitation = Depends(get_invitation_by_id),
    db: Session = Depends(get_db),
):
    """Update a specific invitation."""
    invitation_service = InvitationService(db)
    updated_invitation = invitation_service.update_invitation(
        invitation.id, invitation_data
    )

    if not updated_invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return updated_invitation


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation: Invitation = Depends(get_invitation_by_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept an invitation."""
    from app.commands.invitations.accept_invitation_command import (
        AcceptInvitationCommand,
    )
    from app.exceptions.invitation_exceptions import (
        InvitationException,
        InvitationNotFoundError,
        InvitationExpiredError,
        InvitationUnauthorizedError,
        UserNotFoundError,
    )

    try:
        command = AcceptInvitationCommand(db)
        membership = command.execute(invitation.id, current_user.id)

        # Return the created membership
        return {
            "message": "Invitation accepted successfully",
            "membership_id": str(membership.id),
        }

    except InvitationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (
        InvitationExpiredError,
        InvitationUnauthorizedError,
        UserNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvitationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invitations/{invitation_id}/decline", status_code=status.HTTP_200_OK)
def decline_invitation(
    invitation: Invitation = Depends(get_invitation_by_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decline an invitation."""
    from app.commands.invitations.decline_invitation_command import (
        DeclineInvitationCommand,
    )
    from app.exceptions.invitation_exceptions import (
        InvitationException,
        InvitationNotFoundError,
        InvitationExpiredError,
        InvitationUnauthorizedError,
    )

    try:
        command = DeclineInvitationCommand(db)
        success = command.execute(invitation.id, current_user.email)

        return {
            "message": "Invitation declined successfully",
        }

    except InvitationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InvitationExpiredError, InvitationUnauthorizedError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvitationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def resend_invitation(
    invitation: Invitation = Depends(get_invitation_by_id),
    db: Session = Depends(get_db),
):
    """Resend an invitation by deleting the existing one and creating a new one."""
    from app.commands.invitations.resend_invitation_command import (
        ResendInvitationCommand,
    )

    try:
        command = ResendInvitationCommand(db)
        new_invitation = command.execute(invitation.id)

        if not new_invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        return new_invitation

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invitation(
    invitation: Invitation = Depends(get_invitation_by_id),
    db: Session = Depends(get_db),
):
    """Delete an invitation."""
    invitation_service = InvitationService(db)
    success = invitation_service.delete_invitation(invitation.id)

    if not success:
        raise HTTPException(status_code=404, detail="Invitation not found")


# Utility endpoints
@router.post("/invitations/cleanup", status_code=status.HTTP_200_OK)
def cleanup_expired_invitations(db: Session = Depends(get_db)):
    """Clean up expired invitations."""
    invitation_service = InvitationService(db)
    deleted_count = invitation_service.cleanup_expired_invitations()

    return {
        "message": f"Cleaned up {deleted_count} expired invitations",
        "deleted_count": deleted_count,
    }


@router.get("/workspaces/{workspace_id}/invitations/count")
def get_pending_invitations_count(
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
):
    """Get the count of pending invitations for an workspace."""
    invitation_service = InvitationService(db)
    count = invitation_service.get_pending_invitations_count(workspace.id)

    return {"pending_invitations_count": count}
