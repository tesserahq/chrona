from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal

if TYPE_CHECKING:
    from app.schemas.source import Source
    from app.schemas.source_author import SourceAuthor
    from app.schemas.author import Author
else:
    from app.schemas.source import Source
    from app.schemas.source_author import SourceAuthor
    from app.schemas.author import Author


class EntryBase(BaseModel):
    title: str = Field(..., min_length=1)
    body: Optional[str] = Field(None)
    source_id: UUID = Field(...)
    external_id: str = Field(...)
    tags: Optional[List[str]] = Field(
        None, description="Optional list of tags associated with the entry."
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of labels associated with the entry."
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata dictionary for the entry."
    )
    source_author_id: Optional[UUID] = Field(
        None, description="UUID of the author (user) who created the entry."
    )
    project_id: Optional[UUID] = Field(
        None, description="UUID of the project this entry belongs to."
    )


class EntryCreate(EntryBase):
    pass


class EntryUpdate(BaseModel):
    title: Optional[str] = Field(None)
    body: Optional[str] = None
    source_id: Optional[UUID] = None
    external_id: Optional[str] = None
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


class EntryInDB(EntryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class Entry(EntryInDB):
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

    class Config:
        from_attributes = True


class EntryResponse(EntryInDB):
    """Entry response schema with source and source_author information included."""

    source: Optional[Source] = None
    source_author: Optional[SourceAuthorWithAuthor] = None

    @field_validator("source", mode="before")
    @classmethod
    def get_source_from_model(cls, v, info):
        """Get source object from the model's source relationship."""
        if hasattr(info.data, "source") and info.data.source:
            return info.data.source
        return v

    @field_validator("source_author", mode="before")
    @classmethod
    def get_source_author_from_model(cls, v, info):
        """Get source_author object from the model's source_author relationship."""
        if hasattr(info.data, "source_author") and info.data.source_author:
            return info.data.source_author
        return v

    class Config:
        from_attributes = True


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"]
    value: Any


class EntrySearchFilters(BaseModel):
    title: Optional[Union[str, SearchOperator]] = None
    source_id: Optional[Union[UUID, SearchOperator]] = None
    external_id: Optional[Union[str, SearchOperator]] = None
    source_author_id: Optional[Union[UUID, SearchOperator]] = None
    project_id: Optional[Union[UUID, SearchOperator]] = None


class EntrySearchResponse(BaseModel):
    data: List[EntryResponse]
