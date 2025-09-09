from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from app.schemas.source_author import SourceAuthor
    from app.schemas.author import Author
else:
    from app.schemas.source_author import SourceAuthor
    from app.schemas.author import Author


class CommentBase(BaseModel):
    body: str = Field(..., description="The content of the comment")
    source_author_id: Optional[UUID] = Field(
        None, description="UUID of the author (user) who created the comment."
    )
    entry_id: Optional[UUID] = Field(
        None, description="UUID of the entry this comment belongs to."
    )
    tags: Optional[List[str]] = Field(
        None, description="Optional list of tags associated with the comment."
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of labels associated with the comment."
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata dictionary for the comment."
    )
    external_id: Optional[str] = Field(
        None, description="External ID of the comment from the source system."
    )
    source_id: Optional[UUID] = Field(
        None, description="UUID of the source this comment belongs to."
    )


class CommentCreate(CommentBase):
    body: str = Field(..., description="The content of the comment")
    source_author_id: UUID = Field(
        ..., description="UUID of the author (user) who created the comment."
    )
    entry_id: UUID = Field(
        ..., description="UUID of the entry this comment belongs to."
    )
    tags: Optional[List[str]] = Field(
        None, description="Optional list of tags associated with the comment."
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of labels associated with the comment."
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata dictionary for the comment."
    )
    external_id: str = Field(
        ..., description="External ID of the comment from the source system."
    )
    source_id: UUID = Field(
        ..., description="UUID of the source this comment belongs to."
    )


class CommentUpdate(BaseModel):
    body: Optional[str] = Field(None, description="The content of the comment")
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    external_id: Optional[str] = Field(
        None, description="External ID of the comment from the source system."
    )
    source_id: Optional[UUID] = Field(
        None, description="UUID of the source this comment belongs to."
    )


class CommentInDB(CommentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Comment(CommentInDB):
    pass


class SourceAuthorWithAuthor(SourceAuthor):
    """SourceAuthor schema with author information included."""

    author: Optional[Author] = None

    @field_validator("author", mode="before")
    @classmethod
    def get_author_from_model(cls, v, info):
        """Get author object from the model's author relationship."""
        if hasattr(info.data, "author") and info.data.author:
            return info.data.author
        return v

    model_config = {"from_attributes": True}


class CommentResponse(CommentInDB):
    """Comment response schema with source_author and author information included."""

    source_author: Optional[SourceAuthorWithAuthor] = None

    @field_validator("source_author", mode="before")
    @classmethod
    def get_source_author_from_model(cls, v, info):
        """Get source_author object from the model's source_author relationship."""
        if hasattr(info.data, "source_author") and info.data.source_author:
            return info.data.source_author
        return v

    model_config = {"from_attributes": True}
