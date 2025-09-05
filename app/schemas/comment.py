from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


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


class CommentUpdate(BaseModel):
    body: Optional[str] = Field(None, description="The content of the comment")
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


class CommentInDB(CommentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class Comment(CommentInDB):
    pass
