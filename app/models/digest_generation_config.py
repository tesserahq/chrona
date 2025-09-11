from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

import uuid

from app.db import Base


class DigestGenerationConfig(Base, TimestampMixin, SoftDeleteMixin):
    """DigestGenerationConfig model for managing digest configurations."""

    __tablename__ = "digest_generation_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    filter_tags = Column(ARRAY(String), default=list, nullable=False)
    filter_labels = Column(
        JSONB, default=dict, nullable=False
    )  # Dictionary of filter labels
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    system_prompt = Column(String, nullable=False)
    timezone = Column(String, nullable=False)
    generate_empty_digest = Column(Boolean, default=False, nullable=False)
    cron_expression = Column(String, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="digest_generation_configs")
    digests = relationship("Digest", back_populates="digest_generation_config")
