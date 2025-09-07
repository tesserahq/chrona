from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class SourceBase(BaseModel):
    """Base source schema with common fields."""

    name: str = Field(..., description="Name of the source")
    description: Optional[str] = Field(None, description="Description of the source")
    identifier: str = Field(..., description="Unique identifier for the source")


class SourceCreate(SourceBase):
    """Schema for creating a new source."""

    pass


class SourceUpdate(BaseModel):
    """Schema for updating an existing source."""

    name: Optional[str] = Field(None, description="Name of the source")
    description: Optional[str] = Field(None, description="Description of the source")
    identifier: Optional[str] = Field(
        None, description="Unique identifier for the source"
    )


class Source(SourceBase):
    """Schema for source responses."""

    id: UUID = Field(..., description="Unique identifier for the source")
    workspace_id: UUID = Field(
        ..., description="ID of the workspace this source belongs to"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the source was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the source was last updated"
    )

    class Config:
        from_attributes = True
