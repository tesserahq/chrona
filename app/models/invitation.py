from datetime import datetime, timezone
from typing import cast
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.db import Base
from sqlalchemy.dialects.postgresql import JSONB
from app.constants.membership import MembershipRoles
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Invitation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "invitations"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), nullable=False)
    workspace_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    role = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    inviter_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    expires_at = Column(DateTime, nullable=False)
    # Optional list of project assignments: [{"id": UUID, "role": str}]
    projects = Column(JSONB, nullable=True, server_default="[]")

    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    inviter = relationship(
        "User", foreign_keys=[inviter_id], back_populates="invitations"
    )

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        expires_at_dt = cast(datetime, self.expires_at)
        if expires_at_dt.tzinfo is None:
            expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at_dt

    @property
    def is_valid(self) -> bool:
        """Check if the invitation is valid (not expired)."""
        return not self.is_expired

    @validates("projects")
    def _normalize_projects(self, key, value):
        """Ensure projects JSON is serializable (convert UUIDs to strings)."""
        if value is None:
            return None
        normalized = []
        for item in value:
            if isinstance(item, dict):
                new_item = dict(item)
                if "id" in new_item:
                    try:
                        new_item["id"] = (
                            str(new_item["id"]) if new_item["id"] is not None else None
                        )
                    except Exception:
                        pass
                normalized.append(new_item)
            else:
                normalized.append(item)
        return normalized
