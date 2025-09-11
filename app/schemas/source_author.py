from typing import Optional, Any, List, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class SourceAuthorBase(BaseModel):
    """Base source author schema with common fields."""

    author_id: UUID = Field(..., description="UUID of the author")
    source_id: UUID = Field(..., description="UUID of the source")
    source_author_id: str = Field(..., description="External author ID from the source")


class SourceAuthorCreate(SourceAuthorBase):
    """Schema for creating a new source author."""

    pass


class SourceAuthorUpdate(BaseModel):
    """Schema for updating an existing source author."""

    author_id: Optional[UUID] = Field(None, description="UUID of the author")
    source_id: Optional[UUID] = Field(None, description="UUID of the source")
    source_author_id: Optional[str] = Field(
        None, description="External author ID from the source"
    )


class SourceAuthorInDB(SourceAuthorBase):
    """Schema for source author in database."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceAuthor(SourceAuthorInDB):
    """Schema for source author responses."""

    pass


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"]
    value: Any


class SourceAuthorSearchFilters(BaseModel):
    author_id: Optional[Union[UUID, SearchOperator]] = None
    source_id: Optional[Union[UUID, SearchOperator]] = None
    source_author_id: Optional[Union[str, SearchOperator]] = None


class SourceAuthorSearchResponse(BaseModel):
    data: List[SourceAuthor]
