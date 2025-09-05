from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy_json import mutable_json_type  # type: ignore
from sqlalchemy.dialects.postgresql import JSONB
from app.config import get_settings

import uuid

from app.db import Base


class Entry(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    body = Column(String, nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    external_id = Column(String, nullable=False)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    meta_data = Column(JSONB, default=dict, nullable=False)  # Dictionary of metadata
    source_author_id = Column(
        UUID(as_uuid=True), ForeignKey("source_authors.id"), nullable=False
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Relationships
    source_author = relationship("SourceAuthor", back_populates="entries")
    project = relationship("Project", back_populates="entries")
    source = relationship("Source", back_populates="entries")
    comments = relationship("Comment", back_populates="entry")
