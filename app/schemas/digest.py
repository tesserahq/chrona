from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.constants.digest_constants import DigestStatuses

if TYPE_CHECKING:
    from app.schemas.entry import EntryResponse
    from app.schemas.digest_generation_config import DigestGenerationConfigSummary
else:
    from app.schemas.entry import EntryResponse
    from app.schemas.digest_generation_config import DigestGenerationConfigSummary


class DigestSharedFields(BaseModel):
    """Fields shared across digest payload representations."""

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
    status: str = Field(
        default=DigestStatuses.DRAFT, description="Status of the digest"
    )
    ui_format: Optional[Dict[str, Any]] = Field(
        None, description="UI format for this digest"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time of the digest"
    )
    published_at: Optional[datetime] = Field(
        None, description="Published time of the digest"
    )


class DigestBase(DigestSharedFields):
    """Base digest schema with project linkage."""

    project_id: UUID = Field(
        ..., description="UUID of the project this digest belongs to"
    )


class DigestCreate(DigestBase):
    """Schema for creating a new digest."""

    pass


class ProjectDigestCreateRequest(DigestSharedFields):
    """Schema for creating a digest within a project scope via the API."""

    model_config = ConfigDict(extra="forbid")


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
    published_at: Optional[datetime] = Field(
        None, description="Published time of the digest"
    )


class Digest(DigestBase):
    """Schema for digest response."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    digest_generation_config: Optional[DigestGenerationConfigSummary] = Field(
        None, description="Digest generation config summary with id and ui_format"
    )

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


class DigestWithEntries(Digest):
    """Schema for digest response with entries included."""

    entries: List[EntryResponse] = Field(
        default_factory=list, description="List of entries included in this digest"
    )

    model_config = {"from_attributes": True}


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


class DigestBackfillTaskResponse(BaseModel):
    """Schema for async backfill digests task response."""

    task_id: str = Field(
        ..., description="Celery task ID for tracking the backfill process"
    )
    message: str = Field(..., description="Status message about the backfill task")
    estimated_completion_time: Optional[str] = Field(
        None, description="Estimated completion time for the backfill task"
    )
