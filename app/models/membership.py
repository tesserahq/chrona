from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.constants.membership import ADMIN_ROLE, COLLABORATOR_ROLE, OWNER_ROLE
from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import String

from app.db import Base


class Membership(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    role = Column(String, nullable=False)  # e.g., "owner", "admin", "collaborator"
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="memberships")
    workspace = relationship("Workspace", back_populates="memberships")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def is_owner(self) -> bool:
        """Check if the membership is an owner."""
        return self.role == OWNER_ROLE

    def is_collaborator(self) -> bool:
        """Check if the membership is a collaborator."""
        return self.role == COLLABORATOR_ROLE

    def is_admin(self) -> bool:
        """Check if the membership is an admin."""
        return self.role == ADMIN_ROLE
