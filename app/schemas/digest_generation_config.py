from typing import Optional, Dict, Any, List, Union, Literal
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class DigestGenerationConfigBase(BaseModel):
    """Base digest generation config schema with common fields."""

    title: str = Field(
        ..., min_length=1, description="Title of the digest generation config"
    )
    filter_tags: List[str] = Field(
        default_factory=list, description="Tags to filter entries for this digest"
    )
    filter_labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels to filter entries for this digest"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags associated with this digest generation config",
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Labels for this digest generation config"
    )
    system_prompt: str = Field(..., description="System prompt for digest generation")
    timezone: str = Field(..., description="Timezone for digest scheduling")
    generate_empty_digest: bool = Field(
        default=False,
        description="Whether to generate digest even when no entries match",
    )
    cron_expression: str = Field(
        ..., description="Cron expression for digest scheduling"
    )
    project_id: Optional[UUID] = Field(
        None, description="UUID of the project this digest generation config belongs to"
    )
    ui_format: Optional[Dict[str, Any]] = Field(
        None, description="UI format for this digest generation config"
    )


class DigestGenerationConfigCreate(DigestGenerationConfigBase):
    """Schema for creating a new digest generation config."""

    pass


class DigestGenerationConfigUpdate(BaseModel):
    """Schema for updating a digest generation config."""

    title: Optional[str] = Field(
        None, min_length=1, description="Title of the digest generation config"
    )
    filter_tags: Optional[List[str]] = Field(
        None, description="Tags to filter entries for this digest"
    )
    filter_labels: Optional[Dict[str, Any]] = Field(
        None, description="Labels to filter entries for this digest"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with this digest generation config"
    )
    labels: Optional[Dict[str, Any]] = Field(
        None, description="Labels for this digest generation config"
    )
    system_prompt: Optional[str] = Field(
        None, description="System prompt for digest generation"
    )
    timezone: Optional[str] = Field(None, description="Timezone for digest scheduling")
    generate_empty_digest: Optional[bool] = Field(
        None, description="Whether to generate digest even when no entries match"
    )
    cron_expression: Optional[str] = Field(
        None, description="Cron expression for digest scheduling"
    )
    ui_format: Optional[Dict[str, Any]] = Field(
        None, description="UI format for this digest generation config"
    )


class DigestGenerationConfig(DigestGenerationConfigBase):
    """Schema for digest generation config response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchOperator(BaseModel):
    """Schema for search operators in filters."""

    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"] = Field(
        ...,
        description="The comparison operator to use in the search filter. Supports equality, inequality, comparison, pattern matching, and list operations.",
    )
    value: Any = Field(
        ..., description="The value to compare against using the specified operator."
    )


class DigestGenerationConfigSearchFilters(BaseModel):
    """Schema for digest generation config search filters."""

    title: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by digest generation config title. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    project_id: Optional[Union[UUID, SearchOperator]] = Field(
        None,
        description="Filter by project UUID. Can be a direct UUID match or a SearchOperator for more complex comparisons.",
    )
    timezone: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by timezone. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    generate_empty_digest: Optional[Union[bool, SearchOperator]] = Field(
        None,
        description="Filter by generate_empty_digest flag. Can be a direct boolean match or a SearchOperator for more complex comparisons.",
    )
    cron_expression: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by cron expression. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )


# DigestGenerationConfigSearchResponse is no longer needed as we use Page[DigestGenerationConfig] from fastapi-pagination
