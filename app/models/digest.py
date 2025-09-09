from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

import uuid

from app.db import Base


class Digest(Base, TimestampMixin, SoftDeleteMixin):
    """Digest model for the application."""

    __tablename__ = "digests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    body = Column(String, nullable=True)
    entries_ids = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    comments_ids = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    from_date = Column(DateTime, nullable=True)
    to_date = Column(DateTime, nullable=True)
    digest_generation_config_id = Column(
        UUID(as_uuid=True), ForeignKey("digest_generation_configs.id"), nullable=False
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Relationships
    digest_generation_config = relationship(
        "DigestGenerationConfig", back_populates="digests"
    )
    project = relationship("Project", back_populates="digests")
