from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db import Base


class Workspace(Base, TimestampMixin, SoftDeleteMixin):
    """Workspace model for organizing projects and resources."""

    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    logo = Column(String, nullable=True)  # We'll handle file uploads separately
    identifier = Column(String(100), nullable=True, unique=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    locked = Column(Boolean, default=False, nullable=False)

    # Relationships
    created_by = relationship("User", back_populates="workspaces")
    memberships = relationship(
        "Membership", back_populates="workspace", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="workspace", cascade="all, delete-orphan"
    )
    invitations = relationship(
        "Invitation", back_populates="workspace", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Workspace(id={self.id}, name={self.name})>"
