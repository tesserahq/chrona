from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

import uuid

from app.db import Base


class Source(Base, TimestampMixin, SoftDeleteMixin):
    """Source model for the application."""

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    description = Column(String, nullable=True)
    identifier = Column(String, nullable=False)
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="sources")
    entries = relationship("Entry", back_populates="source")
    import_requests = relationship("ImportRequest", back_populates="source")
    import_request_items = relationship("ImportRequestItem", back_populates="source")
    source_authors = relationship("SourceAuthor", back_populates="source")
    comments = relationship("Comment", back_populates="source")
