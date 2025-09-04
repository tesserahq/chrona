from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.invitation import Invitation
from app.schemas.invitation import InvitationCreate, InvitationUpdate
from app.services.soft_delete_service import SoftDeleteService
from app.exceptions.invitation_exceptions import (
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationUnauthorizedError,
)


class InvitationService(SoftDeleteService[Invitation]):
    def __init__(self, db: Session):
        super().__init__(db, Invitation)

    def create_invitation(
        self, invitation: InvitationCreate, expires_in_hours: int = 24
    ) -> Invitation:
        """Create a new invitation."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        db_invitation = Invitation(**invitation.model_dump(), expires_at=expires_at)

        self.db.add(db_invitation)
        self.db.commit()
        self.db.refresh(db_invitation)

        # Load relationships for the created invitation
        return (
            self.db.query(Invitation)
            .options(joinedload(Invitation.workspace), joinedload(Invitation.inviter))
            .filter(Invitation.id == db_invitation.id)
            .first()
        )

    def get_invitation(self, invitation_id: UUID) -> Optional[Invitation]:
        """Get an invitation by ID."""
        return (
            self.db.query(Invitation)
            .options(joinedload(Invitation.workspace), joinedload(Invitation.inviter))
            .filter(Invitation.id == invitation_id)
            .first()
        )

    def get_invitations_by_workspace(
        self,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 100,
        valid_only: bool = True,
    ) -> List[Invitation]:
        """Get invitations for a specific workspace."""
        query = (
            self.db.query(Invitation)
            .options(joinedload(Invitation.workspace), joinedload(Invitation.inviter))
            .filter(Invitation.workspace_id == workspace_id)
        )

        if valid_only:
            query = query.filter(Invitation.expires_at > datetime.now(timezone.utc))

        return query.offset(skip).limit(limit).all()

    def get_invitations_by_email(
        self, email: str, skip: int = 0, limit: int = 100, valid_only: bool = True
    ) -> List[Invitation]:
        """Get invitations for a specific email address."""
        query = (
            self.db.query(Invitation)
            .options(
                joinedload(Invitation.workspace),
                joinedload(Invitation.inviter),
            )
            .filter(Invitation.email == email)
        )

        if valid_only:
            query = query.filter(Invitation.expires_at > datetime.now(timezone.utc))

        return query.offset(skip).limit(limit).all()

    def update_invitation(
        self, invitation_id: UUID, invitation: InvitationUpdate
    ) -> Optional[Invitation]:
        """Update an existing invitation."""
        db_invitation = (
            self.db.query(Invitation)
            .options(
                joinedload(Invitation.workspace),
                joinedload(Invitation.inviter),
            )
            .filter(Invitation.id == invitation_id)
            .first()
        )

        if db_invitation:
            update_data = invitation.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_invitation, key, value)
            self.db.commit()
            self.db.refresh(db_invitation)

        return db_invitation

    def accept_invitation(self, invitation_id: UUID) -> Optional[Invitation]:
        """Accept an invitation and return it for further processing."""
        invitation = self.get_invitation(invitation_id)

        if not invitation:
            raise InvitationNotFoundError(
                f"Invitation with ID {invitation_id} not found"
            )

        if invitation.is_expired:
            raise InvitationExpiredError("Invitation has expired")

        # Soft delete the invitation
        self.delete_record(invitation_id)

        return invitation

    def decline_invitation(self, invitation_id: UUID, user_email: str) -> bool:
        """Decline an invitation. Only the invited user can decline it."""
        invitation = self.get_invitation(invitation_id)

        if not invitation:
            raise InvitationNotFoundError(
                f"Invitation with ID {invitation_id} not found"
            )

        if invitation.is_expired:
            raise InvitationExpiredError("Invitation has expired")

        if invitation.email != user_email:
            raise InvitationUnauthorizedError(
                "Only the invited user can decline this invitation"
            )

        # Soft delete the invitation
        return self.delete_record(invitation_id)

    def delete_invitation(self, invitation_id: UUID) -> bool:
        """Delete an invitation (soft delete)."""
        return self.delete_record(invitation_id)

    def delete_invitations_by_workspace(self, workspace_id: UUID) -> bool:
        """Delete all invitations for a workspace."""
        # TODO: This could be more efficient by using a bulk delete
        invitations = self.get_invitations_by_workspace(workspace_id)
        invitation_ids = [invitation.id for invitation in invitations]
        return self.delete_records(invitation_ids)

    def hard_delete_invitation(self, invitation_id: UUID) -> bool:
        """Permanently delete an invitation from the database."""
        return self.hard_delete_record(invitation_id)

    def restore_invitation(self, invitation_id: UUID) -> bool:
        """Restore a soft-deleted invitation."""
        return self.restore_record(invitation_id)

    def get_deleted_invitations(
        self, skip: int = 0, limit: int = 100
    ) -> List[Invitation]:
        """Get all soft-deleted invitations."""
        return self.get_deleted_records(skip, limit)

    def get_deleted_invitation(self, invitation_id: UUID) -> Optional[Invitation]:
        """Get a single soft-deleted invitation by ID."""
        return self.get_deleted_record(invitation_id)

    def get_invitation_any_status(self, invitation_id: UUID) -> Optional[Invitation]:
        """Get an invitation regardless of deletion status (deleted or not)."""
        return self.get_record_any_status(invitation_id)

    def cleanup_expired_invitations(self) -> int:
        """Delete all expired invitations. Returns the number of deleted invitations."""
        expired_invitations = (
            self.db.query(Invitation)
            .filter(Invitation.expires_at < datetime.now(timezone.utc))
            .all()
        )

        count = len(expired_invitations)
        for invitation in expired_invitations:
            self.db.delete(invitation)

        self.db.commit()
        return count

    def get_pending_invitations_count(self, workspace_id: UUID) -> int:
        """Get the count of pending (valid, unexpired) invitations for a workspace."""
        return (
            self.db.query(Invitation)
            .filter(
                and_(
                    Invitation.workspace_id == workspace_id,
                    Invitation.expires_at > datetime.now(timezone.utc),
                )
            )
            .count()
        )

    def get_invitations_for_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Invitation]:
        """Get all valid invitations for a user (by email)."""
        # Get user's email
        from app.models.user import User

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Query invitations by email
        query = (
            self.db.query(Invitation)
            .options(
                joinedload(Invitation.workspace),
                joinedload(Invitation.inviter),
            )
            .filter(
                and_(
                    Invitation.email == user.email,
                    Invitation.expires_at > datetime.now(timezone.utc),
                )
            )
        )

        return query.offset(skip).limit(limit).all()
