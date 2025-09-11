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


class EntryUpdateBase(BaseModel):
    body: str = Field(..., description="The content of the entry update")
    source_author_id: Optional[UUID] = Field(
        None, description="UUID of the author (user) who created the entry update."
    )
    entry_id: Optional[UUID] = Field(
        None, description="UUID of the entry this entry update belongs to."
    )
    tags: Optional[List[str]] = Field(
        None, description="Optional list of tags associated with the entry update."
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of labels associated with the entry update."
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata dictionary for the entry update."
    )
    external_id: Optional[str] = Field(
        None, description="External ID of the entry update from the source system."
    )
    source_id: Optional[UUID] = Field(
        None, description="UUID of the source this entry update belongs to."
    )


class EntryUpdateCreate(EntryUpdateBase):
    body: str = Field(..., description="The content of the entry update")
    source_author_id: UUID = Field(
        ..., description="UUID of the author (user) who created the entry update."
    )
    entry_id: UUID = Field(
        ..., description="UUID of the entry this entry update belongs to."
    )
    tags: Optional[List[str]] = Field(
        None, description="Optional list of tags associated with the entry update."
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of labels associated with the entry update."
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata dictionary for the entry update."
    )
    external_id: str = Field(
        ..., description="External ID of the entry update from the source system."
    )
    source_id: UUID = Field(
        ..., description="UUID of the source this entry update belongs to."
    )


class EntryUpdateUpdate(BaseModel):
    body: Optional[str] = Field(None, description="The content of the entry update")
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    external_id: Optional[str] = Field(
        None, description="External ID of the entry update from the source system."
    )
    source_id: Optional[UUID] = Field(
        None, description="UUID of the source this entry update belongs to."
    )


class EntryUpdateInDB(EntryUpdateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntryUpdate(EntryUpdateInDB):
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


class EntryUpdateResponse(EntryUpdateInDB):
    """EntryUpdate response schema with source_author and author information included."""

    source_author: Optional[SourceAuthorWithAuthor] = None

    @field_validator("source_author", mode="before")
    @classmethod
    def get_source_author_from_model(cls, v, info):
        """Get source_author object from the model's source_author relationship."""
        if hasattr(info.data, "source_author") and info.data.source_author:
            return info.data.source_author
        return v

    model_config = {"from_attributes": True}
