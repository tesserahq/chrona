from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, cast, List, Union
from uuid import UUID
from datetime import datetime
from typing import Literal
from app.config import get_settings


class ProjectBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The name of the project. Must be between 1 and 100 characters.",
    )
    description: Optional[str] = Field(
        None, description="Optional description of the project and its purpose."
    )
    workspace_id: Optional[UUID] = Field(
        None, description="The UUID of the workspace this project belongs to."
    )
    labels: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional labels for the project. This can be used to store arbitrary data about the project.",
    )


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None


class ProjectInDB(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Project(ProjectInDB):
    pass


class SearchOperator(BaseModel):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "ilike", "in", "not in"] = Field(
        ...,
        description="The comparison operator to use in the search filter. Supports equality, inequality, comparison, pattern matching, and list operations.",
    )
    value: Any = Field(
        ..., description="The value to compare against using the specified operator."
    )


class ProjectSearchFilters(BaseModel):
    name: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by project name. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    description: Optional[Union[str, SearchOperator]] = Field(
        None,
        description="Filter by project description. Can be a direct string match or a SearchOperator for more complex comparisons.",
    )
    workspace_id: Optional[Union[UUID, SearchOperator]] = Field(
        None,
        description="Filter by workspace UUID. Can be a direct UUID match or a SearchOperator for more complex comparisons.",
    )


class ProjectSearchResponse(BaseModel):
    data: List[Project] = Field(
        ..., description="List of projects matching the search criteria."
    )
