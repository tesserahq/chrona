from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class SectionBase(BaseModel):
    """Base section schema with common fields."""

    header: str = Field(..., min_length=1, description="Header of the section")
    subheader: Optional[str] = Field(None, description="Subheader of the section")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with this section"
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for this section"
    )
    gazette_id: UUID = Field(
        ..., description="UUID of the gazette this section belongs to"
    )


class SectionCreate(SectionBase):
    """Schema for creating a new section."""

    pass


class SectionUpdate(BaseModel):
    """Schema for updating a section."""

    header: Optional[str] = Field(
        None, min_length=1, description="Header of the section"
    )
    subheader: Optional[str] = Field(None, description="Subheader of the section")
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with this section"
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Labels for this section"
    )


class Section(SectionBase):
    """Schema for section responses."""

    id: UUID = Field(..., description="Unique identifier for the section")
    created_at: datetime = Field(
        ..., description="Timestamp when the section was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the section was last updated"
    )
    deleted_at: Optional[datetime] = Field(
        None, description="Timestamp when the section was soft deleted"
    )

    model_config = {"from_attributes": True}


class SectionWithDigests(BaseModel):
    """Schema for section responses with associated digests."""

    section: Section
    digests: List["Digest"] = Field(
        default_factory=list,
        description="Published digests from the project that match the section's tags/labels",
    )

    model_config = {"from_attributes": True}


# Import Digest schema for forward reference
from app.schemas.digest import Digest

SectionWithDigests.model_rebuild()
