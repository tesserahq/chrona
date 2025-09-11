from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

import uuid

from app.db import Base


class Project(Base, TimestampMixin, SoftDeleteMixin):
    """Project model for the application."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    description = Column(String, nullable=True)
    logo = Column(String, nullable=True)  # We'll handle file uploads separately
    labels = Column(JSONB, default=dict, nullable=False)  # Dictionary of labels
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    quore_project_id = Column(String, nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    memberships = relationship(
        "ProjectMembership", back_populates="project", cascade="all, delete-orphan"
    )
    entries = relationship("Entry", back_populates="project")
    import_requests = relationship("ImportRequest", back_populates="project")
    digest_generation_configs = relationship(
        "DigestGenerationConfig", back_populates="project", cascade="all, delete-orphan"
    )
    digests = relationship("Digest", back_populates="project")
