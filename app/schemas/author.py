from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class AuthorBase(BaseModel):
    """Base author schema with common fields."""

    display_name: str = Field(..., description="Display name of the author")
    avatar_url: str = Field(..., description="URL of the author's avatar")
    email: str = Field(..., description="Email address of the author")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the author"
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for the author"
    )
    meta_data: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata for the author"
    )


class AuthorCreate(AuthorBase):
    """Schema for creating a new author."""

    user_id: Optional[UUID] = Field(
        None, description="Optional user ID if author is linked to a user"
    )


class AuthorUpdate(BaseModel):
    """Schema for updating an existing author."""

    display_name: Optional[str] = Field(None, description="Display name of the author")
    avatar_url: Optional[str] = Field(None, description="URL of the author's avatar")
    email: Optional[str] = Field(None, description="Email address of the author")
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with the author"
    )
    labels: Optional[Dict[str, Any]] = Field(None, description="Labels for the author")
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Metadata for the author"
    )
    user_id: Optional[UUID] = Field(
        None, description="Optional user ID if author is linked to a user"
    )


class AuthorMerge(BaseModel):
    """Schema for merging multiple authors into one."""

    author_ids: List[UUID] = Field(
        ...,
        min_length=1,
        description="List of author IDs to merge (must contain at least one)",
    )
    merge_to_author_id: UUID = Field(
        ..., description="ID of the author to merge into (target author)"
    )


class Author(AuthorBase):
    """Schema for author responses."""

    id: UUID = Field(..., description="Unique identifier for the author")
    workspace_id: UUID = Field(
        ..., description="ID of the workspace this author belongs to"
    )
    user_id: Optional[UUID] = Field(
        None, description="Optional user ID if author is linked to a user"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the author was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the author was last updated"
    )

    model_config = {"from_attributes": True}
