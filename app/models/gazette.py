from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

import uuid

from app.db import Base


class Gazette(Base, TimestampMixin, SoftDeleteMixin):
    """Gazette model for the application."""

    __tablename__ = "gazettes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    header = Column(String, nullable=False)
    subheader = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    share_key = Column(String, unique=True, nullable=True)

    project = relationship("Project", back_populates="gazettes")
