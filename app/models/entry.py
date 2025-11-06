from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB

import uuid

from app.db import Base
from app.models.entry_update import EntryUpdate


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
    source_assignee_id = Column(
        UUID(as_uuid=True), ForeignKey("source_authors.id"), nullable=True
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    source_created_at = Column(DateTime, nullable=True)
    source_updated_at = Column(DateTime, nullable=True)
    last_update_created_at = Column(DateTime, nullable=True)

    # Relationships
    source_author = relationship(
        "SourceAuthor", foreign_keys=[source_author_id], back_populates="entries"
    )
    source_assignee = relationship(
        "SourceAuthor", foreign_keys=[source_assignee_id], back_populates="entries"
    )
    project = relationship("Project", back_populates="entries")
    source = relationship("Source", back_populates="entries")
    entry_updates = relationship(
        "EntryUpdate",
        back_populates="entry",
        order_by=EntryUpdate.source_created_at.desc(),
        lazy="selectin",
    )
