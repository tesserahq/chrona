from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
from app.constants.digest_constants import DigestStatuses


class DigestBase(BaseModel):
    """Base digest schema with common fields."""

    title: str = Field(..., min_length=1, description="Title of the digest")
    body: Optional[str] = Field(None, description="Body content of the digest")
    raw_body: Optional[str] = Field(None, description="Raw body content of the digest")
    entries_ids: List[UUID] = Field(
        default_factory=list, description="List of entry IDs included in this digest"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with this digest"
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for this digest"
    )
    entry_updates_ids: List[UUID] = Field(
        default_factory=list,
        description="List of entry_update IDs included in this digest",
    )
    from_date: Optional[datetime] = Field(
        None, description="Start date for the digest period"
    )
    to_date: Optional[datetime] = Field(
        None, description="End date for the digest period"
    )
    digest_generation_config_id: UUID = Field(
        ...,
        description="UUID of the digest generation config used to create this digest",
    )
    project_id: UUID = Field(
        ..., description="UUID of the project this digest belongs to"
    )
    status: str = Field(
        default=DigestStatuses.DRAFT, description="Status of the digest"
    )
    ui_format: Optional[Dict[str, Any]] = Field(
        None, description="UI format for this digest"
    )


class DigestCreate(DigestBase):
    """Schema for creating a new digest."""

    pass


class DigestUpdate(BaseModel):
    """Schema for updating a digest."""

    title: Optional[str] = Field(None, min_length=1, description="Title of the digest")
    body: Optional[str] = Field(None, description="Body content of the digest")
    raw_body: Optional[str] = Field(None, description="Raw body content of the digest")
    entries_ids: Optional[List[UUID]] = Field(
        None, description="List of entry IDs included in this digest"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with this digest"
    )
    labels: Optional[Dict[str, Any]] = Field(None, description="Labels for this digest")
    entry_updates_ids: Optional[List[UUID]] = Field(
        None, description="List of entry_update IDs included in this digest"
    )
    from_date: Optional[datetime] = Field(
        None, description="Start date for the digest period"
    )
    to_date: Optional[datetime] = Field(
        None, description="End date for the digest period"
    )
    project_id: Optional[UUID] = Field(
        None, description="UUID of the project this digest belongs to"
    )
    status: Optional[str] = Field(None, description="Status of the digest")
    ui_format: Optional[Dict[str, Any]] = Field(
        None, description="UI format for this digest"
    )


class Digest(DigestBase):
    """Schema for digest response."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DigestBackfillRequest(BaseModel):
    """Schema for backfilling digests request."""

    days: int = Field(
        ..., gt=0, le=365, description="Number of days to backfill digests for (1-365)"
    )
    start_from_date: Optional[datetime] = Field(
        None,
        description="Date to start backfilling from (defaults to now if not provided)",
    )
    force: bool = Field(
        default=False,
        description="If True, generate digests even if they already exist",
    )


class DigestBackfillResponse(BaseModel):
    """Schema for backfill digests response."""

    created_count: int = Field(..., description="Number of digests created")
    skipped_count: int = Field(
        ..., description="Number of digests skipped (already existed)"
    )
    failed_count: int = Field(
        ..., description="Number of digests that failed to create"
    )
    digests: List[Digest] = Field(..., description="List of created digests")
