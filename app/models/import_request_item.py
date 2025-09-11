from app.models.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

import uuid

from app.db import Base


class ImportRequestItem(Base, TimestampMixin, SoftDeleteMixin):
    """Entry model for the application."""

    __tablename__ = "import_request_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_request_id = Column(
        UUID(as_uuid=True), ForeignKey("import_requests.id"), nullable=False
    )
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    source_item_id = Column(String, nullable=False)
    raw_payload = Column(JSONB, default=dict, nullable=False)
    status = Column(String, nullable=False)

    # Relationships
    import_request = relationship("ImportRequest", back_populates="items")
    source = relationship("Source", back_populates="import_request_items")
