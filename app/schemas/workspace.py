from app.schemas.user import UserDetails
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class WorkspaceBase(BaseModel):
    """Base workspace model containing common workspace attributes."""

    name: str = Field(..., min_length=1, max_length=100)
    """Name of the workspace. Must be between 1 and 100 characters."""

    description: Optional[str] = None
    """Optional description of the workspace."""

    logo: Optional[str] = None
    """Optional URL to the workspace's logo image."""

    identifier: Optional[str] = Field(None, min_length=1, max_length=100)
    """Optional unique identifier for the workspace. Must be a slug-like string."""

    created_by_id: Optional[UUID] = None
    """ID of the user who created the workspace."""

    locked: Optional[bool] = False
    """Whether the workspace is locked and cannot be deleted."""

    quore_workspace_id: Optional[str] = None
    """Updated workspace Quore ID."""


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace. Inherits all fields from WorkspaceBase."""

    created_by_id: Optional[UUID] = None
    """ID of the user who created the workspace. If not provided, will be set to the current user."""


class WorkspaceUpdate(BaseModel):
    """Schema for updating an existing workspace. All fields are optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    """Updated workspace name. Must be between 1 and 100 characters if provided."""

    description: Optional[str] = None
    """Updated workspace description."""

    logo: Optional[str] = None
    """Updated workspace logo URL."""

    identifier: Optional[str] = Field(None, min_length=1, max_length=100)
    """Updated workspace identifier. Must be a unique slug-like string if provided."""

    locked: Optional[bool] = None
    """Whether the workspace is locked and cannot be deleted."""

    quore_workspace_id: Optional[str] = None
    """Updated workspace Quore ID."""


class WorkspaceInDB(WorkspaceBase):
    """Schema representing a workspace as stored in the database. Includes database-specific fields."""

    id: UUID
    """Unique identifier for the workspace in the database."""

    created_at: datetime
    """Timestamp when the workspace was created."""

    updated_at: datetime
    """Timestamp when the workspace was last updated."""

    model_config = {"from_attributes": True}


class Workspace(WorkspaceInDB):
    """Schema for workspace data returned in API responses. Includes creator details."""

    created_by: Optional[UserDetails]
    """Details of the user who created the workspace."""


class WorkspaceStats(BaseModel):
    """Schema for workspace statistics returned by the stats endpoint."""

    project_stats: "ProjectStats" = Field(..., description="Project statistics")


class ProjectStats(BaseModel):
    """Project statistics."""

    total_projects: int = Field(
        ..., description="Total number of projects in the workspace"
    )
    recent_projects: List["ProjectSummary"] = Field(
        ..., description="5 most recently updated projects"
    )


class ProjectSummary(BaseModel):
    """Summary information for a project in stats."""

    id: UUID
    name: str
    description: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptStats(BaseModel):
    """Prompt statistics."""

    total_prompts: int = Field(
        ..., description="Total number of prompts in the workspace"
    )
    recent_prompts: List["PromptSummary"] = Field(
        ..., description="5 most recently updated prompts"
    )


class PromptSummary(BaseModel):
    """Summary information for a prompt in stats."""

    id: UUID
    name: str
    type: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class PluginStats(BaseModel):
    """Plugin statistics."""

    total_enabled: int = Field(..., description="Total number of enabled plugins")
    total_disabled: int = Field(..., description="Total number of disabled plugins")


class CredentialStats(BaseModel):
    """Credential statistics."""

    total_credentials: int = Field(..., description="Total number of credentials")
    recent_credentials: List["CredentialSummary"] = Field(
        ..., description="5 most recently updated credentials"
    )


class CredentialSummary(BaseModel):
    """Summary information for a credential in stats."""

    id: UUID
    name: str
    type: str
    updated_at: datetime
