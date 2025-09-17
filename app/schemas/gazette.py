from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime
from typing import Literal


class GazetteBase(BaseModel):
    header: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="The header of the gazette. Must be between 1 and 255 characters.",
    )
    subheader: Optional[str] = Field(
        default=None, max_length=255, description="Optional subheader of the gazette."
    )
    theme: Optional[str] = Field(
        default=None, max_length=100, description="Optional theme for the gazette."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of tags associated with the gazette.",
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of labels for storing arbitrary data about the gazette.",
    )
    project_id: UUID = Field(
        ..., description="The UUID of the project this gazette belongs to."
    )
    share_key: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional unique share key for the gazette.",
    )


class GazetteCreate(GazetteBase):
    pass


class GazetteUpdate(BaseModel):
    header: Optional[str] = Field(None, min_length=1, max_length=255)
    subheader: Optional[str] = Field(None, max_length=255)
    theme: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    share_key: Optional[str] = Field(None, max_length=100)


class GazetteInDB(GazetteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Gazette(BaseModel):
    """Public gazette response schema that excludes share_key."""

    id: UUID
    header: str
    subheader: Optional[str] = None
    theme: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    labels: Dict[str, Any] = Field(default_factory=dict)
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"] = Field(
        ...,
        description="The comparison operator to use in the search filter. Supports equality, inequality, comparison, pattern matching, and list operations.",
    )
    value: Any = Field(
        ..., description="The value to compare against using the specified operator."
    )


class GazetteSearchFilters(BaseModel):
    header: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by gazette header. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    subheader: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by gazette subheader. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    theme: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by gazette theme. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    project_id: Optional[Union[UUID, SearchOperator]] = Field(
        None,
        description="Filter by project UUID. Can be a direct UUID match or a SearchOperator for more complex comparisons.",
    )
    share_key: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by share key. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )


class GazetteSearchResponse(BaseModel):
    data: List[Gazette] = Field(
        ..., description="List of gazettes matching the search criteria."
    )


class GazetteShare(GazetteInDB):
    """Special response schema for share endpoint that includes share_key."""

    pass  # Inherits all fields including share_key


class GazetteWithDigests(BaseModel):
    """Response schema for gazette with associated digests."""

    gazette: Gazette
    digests: List["Digest"] = Field(
        default_factory=list,
        description="Published digests from the project that match the gazette's tags/labels",
    )

    model_config = {"from_attributes": True}


class GazetteWithSectionsAndDigests(BaseModel):
    """Response schema for gazette with sections and their associated digests."""

    gazette: Gazette
    digests: List["Digest"] = Field(
        default_factory=list,
        description="Published digests from the project that match the gazette's tags/labels",
    )
    sections: List["SectionWithDigests"] = Field(
        default_factory=list,
        description="Sections belonging to this gazette, each with their matching digests",
    )

    model_config = {"from_attributes": True}


# Import schemas for forward references
from app.schemas.digest import Digest
from app.schemas.section import SectionWithDigests

GazetteWithDigests.model_rebuild()
GazetteWithSectionsAndDigests.model_rebuild()
