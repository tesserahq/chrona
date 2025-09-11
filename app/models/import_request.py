from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

import uuid

from app.db import Base


class ImportRequest(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "import_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    requested_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)
    received_count = Column(Integer, nullable=False)
    success_count = Column(Integer, nullable=False)
    failure_count = Column(Integer, nullable=False)
    options = Column(JSONB, default=dict, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Relationships
    user = relationship(
        "User", foreign_keys=[requested_by_id], back_populates="import_requests"
    )
    project = relationship("Project", back_populates="import_requests")
    source = relationship("Source", back_populates="import_requests")
    items = relationship("ImportRequestItem", back_populates="import_request")
