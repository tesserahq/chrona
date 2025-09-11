from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class ImportAuthorData(BaseModel):
    """Schema for author data in import payload."""

    id: str = Field(..., description="External author ID")
    display_name: str = Field(..., description="Display name of the author")
    avatar_url: str = Field(..., description="URL of the author's avatar")
    email: str = Field(..., description="Email address of the author")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the author"
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for the author"
    )
    meta_data: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata for the author"
    )


class ImportEntryUpdateData(BaseModel):
    """Schema for entry update data in import payload."""

    id: str = Field(..., description="External entry update ID")
    body: str = Field(..., description="Body content of the entry update")
    created_at: str = Field(..., description="Creation timestamp of the entry update")
    author: ImportAuthorData = Field(
        ..., description="Author information for the entry update"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the entry update"
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for the entry update"
    )


class ImportItemData(BaseModel):
    """Schema for individual item data in import payload."""

    source: str = Field(..., description="Source identifier (e.g., 'github')")
    title: str = Field(..., description="Title of the item")
    body: str = Field(..., description="Body content of the item")
    tags: List[str] = Field(default_factory=list, description="Tags for the item")
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for the item"
    )
    meta_data: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata for the item"
    )
    author: ImportAuthorData = Field(..., description="Author information for the item")
    entry_updates: List[ImportEntryUpdateData] = Field(
        default_factory=list, description="Entry updates associated with the item"
    )


class ImportItemRequest(BaseModel):
    """Schema for the project import request payload."""

    items: List[ImportItemData] = Field(..., description="List of items to import")


class ImportItemResponse(BaseModel):
    """Schema for the project import response."""

    id: UUID = Field(..., description="ID of the created import request")
    total_items: int = Field(..., description="Total number of items to import")
    processed_items: int = Field(..., description="Number of items processed")
    success_count: int = Field(
        ..., description="Number of successfully processed items"
    )
    failure_count: int = Field(..., description="Number of failed items")
    status: str = Field(..., description="Status of the import request")
