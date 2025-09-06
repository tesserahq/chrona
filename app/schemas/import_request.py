from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


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
    pass


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


class ImportRequestSearchResponse(BaseModel):
    data: List[ImportRequest]
