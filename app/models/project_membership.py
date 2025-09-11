from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.constants.membership import (
    ADMIN_ROLE,
    COLLABORATOR_ROLE,
)
from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import String
from typing import cast

from app.db import Base


class ProjectMembership(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "project_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    role = Column(String, nullable=False)  # e.g., "owner", "admin", "collaborator"
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="project_memberships"
    )
    project = relationship("Project", back_populates="memberships")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def is_collaborator(self) -> bool:
        """Check if the membership is a collaborator."""
        role_value = cast(str, self.role)
        return role_value == COLLABORATOR_ROLE

    def is_admin(self) -> bool:
        """Check if the membership is an admin."""
        role_value = cast(str, self.role)
        return role_value == ADMIN_ROLE
