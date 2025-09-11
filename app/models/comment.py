from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB

import uuid

from app.db import Base


class Comment(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body = Column(String, nullable=False)
    source_author_id = Column(
        UUID(as_uuid=True), ForeignKey("source_authors.id"), nullable=False
    )
    entry_id = Column(UUID(as_uuid=True), ForeignKey("entries.id"), nullable=False)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    meta_data = Column(JSONB, default=dict, nullable=False)  # Dictionary of metadata
    external_id = Column(String, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)

    # Relationships
    source_author = relationship("SourceAuthor", back_populates="comments")
    entry = relationship("Entry", back_populates="comments")
    source = relationship("Source", back_populates="comments")
