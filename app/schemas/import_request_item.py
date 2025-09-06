from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class ImportRequestItemBase(BaseModel):
    import_request_id: UUID = Field(
        ..., description="UUID of the parent import request"
    )
    source_id: UUID = Field(
        ..., description="UUID of the source this import request item belongs to"
    )
    source_item_id: str = Field(..., min_length=1, max_length=200)
    raw_payload: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Raw data from the external source"
    )
    status: str = Field(..., min_length=1, max_length=50)


class ImportRequestItemCreate(ImportRequestItemBase):
    pass


class ImportRequestItemUpdate(BaseModel):
    source_id: Optional[UUID] = Field(
        None, description="UUID of the source this import request item belongs to"
    )
    source_item_id: Optional[str] = Field(None, min_length=1, max_length=200)
    raw_payload: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, min_length=1, max_length=50)


class ImportRequestItemInDB(ImportRequestItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class ImportRequestItem(ImportRequestItemInDB):
    pass


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"]
    value: Any


class ImportRequestItemSearchFilters(BaseModel):
    import_request_id: Optional[Union[UUID, SearchOperator]] = None
    source_id: Optional[Union[UUID, SearchOperator]] = None
    source_item_id: Optional[Union[str, SearchOperator]] = None
    status: Optional[Union[str, SearchOperator]] = None
    created_entry_id: Optional[Union[UUID, SearchOperator]] = None
    created_comment_id: Optional[Union[UUID, SearchOperator]] = None


class ImportRequestItemSearchResponse(BaseModel):
    data: List[ImportRequestItem]
