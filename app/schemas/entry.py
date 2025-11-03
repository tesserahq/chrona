from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal

if TYPE_CHECKING:
    from app.schemas.source import Source
    from app.schemas.source_author import SourceAuthor
    from app.schemas.author import Author
    from app.schemas.entry_update import EntryUpdateResponse
else:
    from app.schemas.source import Source
    from app.schemas.source_author import SourceAuthor
    from app.schemas.author import Author
    from app.schemas.entry_update import EntryUpdateResponse


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
    source_assignee_id: Optional[UUID] = Field(
        None, description="UUID of the assignee (user) for the entry."
    )
    project_id: Optional[UUID] = Field(
        None, description="UUID of the project this entry belongs to."
    )
    source_created_at: Optional[datetime] = Field(
        None,
        description="The date and time the entry was created in the source system.",
    )
    source_updated_at: Optional[datetime] = Field(
        None,
        description="The date and time the entry was updated in the source system.",
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
    source_author_id: Optional[UUID] = None
    source_assignee_id: Optional[UUID] = None
    source_created_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None


class EntryInDB(EntryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


class EntryResponse(EntryInDB):
    """Entry response schema with source, source_author, source_assignee, and entry updates information included."""

    source: Optional[Source] = None
    source_author: Optional[SourceAuthorWithAuthor] = None
    source_assignee: Optional[SourceAuthorWithAuthor] = None
    entry_updates: Optional[List[EntryUpdateResponse]] = None

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

    @field_validator("source_assignee", mode="before")
    @classmethod
    def get_source_assignee_from_model(cls, v, info):
        """Get source_assignee object from the model's source_assignee relationship."""
        if hasattr(info.data, "source_assignee") and info.data.source_assignee:
            return info.data.source_assignee
        return v

    @field_validator("entry_updates", mode="before")
    @classmethod
    def get_entry_updates_from_model(cls, v, info):
        """Get entry updates list from the model's entry_updates relationship."""
        if hasattr(info.data, "entry_updates") and info.data.entry_updates:
            return info.data.entry_updates
        return v

    model_config = {"from_attributes": True}


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"]
    value: Any


class DateRangeFilter(BaseModel):
    """Schema for date range filter settings."""

    from_date: datetime = Field(
        ..., alias="from", description="Start date for the filter"
    )
    to_date: datetime = Field(..., alias="to", description="End date for the filter")

    model_config = {"populate_by_name": True}


class EntrySearchFilters(BaseModel):
    title: Optional[Union[str, SearchOperator]] = None
    source_id: Optional[Union[UUID, SearchOperator]] = None
    external_id: Optional[Union[str, SearchOperator]] = None
    source_author_id: Optional[Union[UUID, SearchOperator]] = None
    project_id: Optional[Union[UUID, SearchOperator]] = None
    tags: Optional[Union[List[str], SearchOperator]] = Field(
        None,
        description="Filter by tags. Can be a list of tags (finds entries with ANY of these tags) or a SearchOperator.",
    )
    created_at: Optional[Union[datetime, SearchOperator, DateRangeFilter]] = Field(
        None,
        description="Filter by entry creation date. Can be a direct datetime value, a SearchOperator with >=, <=, etc., or a DateRangeFilter with 'from' and 'to' fields.",
    )
    updated_at: Optional[Union[datetime, SearchOperator, DateRangeFilter]] = Field(
        None,
        description="Filter by entry update date. Can be a direct datetime value, a SearchOperator with >=, <=, etc., or a DateRangeFilter with 'from' and 'to' fields.",
    )


# EntrySearchResponse is no longer needed as we use Page[EntryResponse] from fastapi-pagination
