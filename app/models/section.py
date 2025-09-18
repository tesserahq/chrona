from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

import uuid

from app.db import Base


class Section(Base, TimestampMixin, SoftDeleteMixin):
    """Section model for the application."""

    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    header = Column(String, nullable=False)
    subheader = Column(String, nullable=True)
    tags = Column(ARRAY(String), default=list, nullable=False)
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    gazette_id = Column(UUID(as_uuid=True), ForeignKey("gazettes.id"), nullable=False)

    gazette = relationship("Gazette", back_populates="sections")
