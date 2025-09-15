from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.user import User
from app.schemas.source import Source
from app.schemas.import_request_item import ImportRequestItem


class ImportRequestBase(BaseModel):
    source_id: UUID = Field(
        ..., description="UUID of the source this import belongs to"
    )
    requested_by_id: UUID = Field(
        ..., description="UUID of the user who requested the import"
    )
    status: str = Field(..., min_length=1, max_length=50)
    received_count: int = Field(..., ge=0)
    success_count: int = Field(..., ge=0)
    failure_count: int = Field(..., ge=0)
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional configuration for the import"
    )
    finished_at: Optional[datetime] = Field(
        None, description="When the import was completed"
    )
    project_id: UUID = Field(
        ..., description="UUID of the project this import belongs to"
    )


class ImportRequestCreate(ImportRequestBase):
    pass


class ImportRequestUpdate(BaseModel):
    source_id: Optional[UUID] = Field(
        None, description="UUID of the source this import belongs to"
    )
    status: Optional[str] = Field(None, min_length=1, max_length=50)
    received_count: Optional[int] = Field(None, ge=0)
    success_count: Optional[int] = Field(None, ge=0)
    failure_count: Optional[int] = Field(None, ge=0)
    options: Optional[Dict[str, Any]] = None
    finished_at: Optional[datetime] = None


class ImportRequestInDB(ImportRequestBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ImportRequest(ImportRequestInDB):
    source: Optional[Source] = Field(
        None, description="Source object associated with this import request"
    )
    requested_by: Optional[User] = Field(
        None, description="User who requested this import"
    )
    items: Optional[List[ImportRequestItem]] = Field(
        None, description="Items associated with this import request"
    )


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"]
    value: Any


class ImportRequestSearchFilters(BaseModel):
    source_id: Optional[Union[UUID, SearchOperator]] = None
    status: Optional[Union[str, SearchOperator]] = None
    requested_by_id: Optional[Union[UUID, SearchOperator]] = None
    project_id: Optional[Union[UUID, SearchOperator]] = None
    received_count: Optional[Union[int, SearchOperator]] = None
    success_count: Optional[Union[int, SearchOperator]] = None
    failure_count: Optional[Union[int, SearchOperator]] = None


# ImportRequestSearchResponse is no longer needed as we use Page[ImportRequest] from fastapi-pagination


class ProcessedItemResult(BaseModel):
    """Schema for individual processed item result."""

    item_id: str = Field(..., description="ID of the processed item")
    success: bool = Field(
        ..., description="Whether the item was processed successfully"
    )
    author_id: Optional[UUID] = Field(None, description="ID of the created author")
    entry_id: Optional[UUID] = Field(None, description="ID of the created entry")
    entry_update_ids: List[UUID] = Field(
        default_factory=list, description="IDs of created entry_updates"
    )
    source_author_id: Optional[UUID] = Field(
        None, description="ID of the created source author"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")


class ImportRequestProcessResponse(BaseModel):
    """Schema for import request processing response."""

    success: bool = Field(
        ..., description="Whether the overall processing was successful"
    )
    import_request_id: Optional[UUID] = Field(
        None, description="ID of the processed import request"
    )
    total_items: Optional[int] = Field(
        None, description="Total number of items to process"
    )
    processed_items_count: Optional[int] = Field(
        None, description="Number of items processed"
    )
    success_count: Optional[int] = Field(
        None, description="Number of successfully processed items"
    )
    failure_count: Optional[int] = Field(None, description="Number of failed items")
    status: Optional[str] = Field(
        None, description="Final status of the import request"
    )
    processed_items: Optional[List[ProcessedItemResult]] = Field(
        None, description="Details of processed items"
    )
    errors: List[str] = Field(
        default_factory=list, description="List of error messages"
    )
    error: Optional[str] = Field(
        None, description="Single error message for simple failures"
    )
