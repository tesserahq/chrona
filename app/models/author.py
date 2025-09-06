from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy_json import mutable_json_type  # type: ignore
from sqlalchemy.dialects.postgresql import JSONB
from app.config import get_settings

import uuid

from app.db import Base


class Author(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=False)
    email = Column(String, nullable=False)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    meta_data = Column(
        "meta_data", JSONB, default=dict, nullable=False
    )  # Dictionary of metadata
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    # Authors could also have a user from the system, this is optional
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="authors")
    user = relationship("User", back_populates="authors")
    source_authors = relationship("SourceAuthor", back_populates="author")
