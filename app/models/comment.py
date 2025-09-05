from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy_json import mutable_json_type  # type: ignore
from sqlalchemy.dialects.postgresql import JSONB
from app.config import get_settings

import uuid

from app.db import Base


class Comment(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body = Column(String, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("entries.id"), nullable=False)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    meta_data = Column(
        "meta_data", JSONB, default=dict, nullable=False
    )  # Dictionary of metadata

    # Relationships
    author = relationship("User", back_populates="comments")
    entry = relationship("Entry", back_populates="comments")
