from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy_json import mutable_json_type  # type: ignore
from sqlalchemy.dialects.postgresql import JSONB
from app.config import get_settings

import uuid

from app.db import Base


class SourceAuthor(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "source_authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    source_author_id = Column(String, nullable=False)

    # Relationships
    author = relationship("Author", back_populates="source_authors")
    comments = relationship("Comment", back_populates="source_author")
    entries = relationship("Entry", back_populates="source_author")
    source = relationship("Source", back_populates="source_authors")
