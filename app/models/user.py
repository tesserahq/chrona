from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, Boolean, DateTime, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

import uuid

from app.db import Base
from app.models.membership import Membership
from app.models.comment import Comment
from app.models.project_membership import ProjectMembership


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for the application.
    This model represents a user in the system and includes fields for
    personal information, authentication, and relationships with other models.
    """

    __tablename__ = "users"

    __table_args__ = (
        Index(
            "uq_users_external_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    external_id = Column(String, nullable=True)

    # Relationships
    workspaces = relationship("Workspace", back_populates="created_by")
    memberships = relationship(
        "Membership", foreign_keys=[Membership.user_id], back_populates="user"
    )
    invitations = relationship(
        "Invitation", back_populates="inviter", cascade="all, delete-orphan"
    )
    project_memberships = relationship(
        "ProjectMembership",
        foreign_keys=[ProjectMembership.user_id],
        back_populates="user",
        cascade="all, delete-orphan",
    )
    entries = relationship("Entry", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}"
