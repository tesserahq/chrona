from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from app.schemas.user import User
else:
    from app.schemas.user import User


class RoleData(BaseModel):
    """Schema for individual role data."""

    id: str
    """Role identifier."""

    name: str
    """Display name for the role."""


class RolesResponse(BaseModel):
    """Schema for the roles endpoint response."""

    roles: List[RoleData]
    """List of available roles."""


class MembershipBase(BaseModel):
    """Base membership model containing common membership attributes."""

    user_id: UUID
    """ID of the user who is a member of the workspace."""

    workspace_id: UUID
    """ID of the workspace the user is a member of."""

    role: str = "member"
    """Role of the user in the workspace. Defaults to 'member'. Other common roles include 'owner' and 'admin'."""

    created_by_id: UUID
    """ID of the user who created the membership."""


class MembershipCreate(MembershipBase):
    """Schema for creating a new membership. Inherits all fields from MembershipBase."""

    pass


class MembershipCreateRequest(BaseModel):
    """Schema for creating a new membership. Inherits all fields from MembershipBase."""

    user_id: UUID
    """ID of the user who is a member of the workspace."""

    role: str = "member"


class MembershipUpdate(BaseModel):
    """Schema for updating an existing membership. All fields are optional."""

    role: Optional[str] = None
    """Updated role for the user in the workspace."""


class MembershipInDB(MembershipBase):
    """Schema representing a membership as stored in the database. Includes database-specific fields."""

    id: UUID
    """Unique identifier for the membership in the database."""

    created_at: datetime
    """Timestamp when the membership was created."""

    updated_at: datetime
    """Timestamp when the membership was last updated."""

    model_config = {"from_attributes": True}


class MembershipResponse(MembershipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    user: Optional["User"] = None
    created_by: Optional["User"] = None

    @field_validator("user", mode="before")
    @classmethod
    def get_user_from_model(cls, v, info):
        """Get user object from the model's user relationship."""
        if hasattr(info.data, "user") and info.data.user:
            return info.data.user
        return v

    @field_validator("created_by", mode="before")
    @classmethod
    def get_created_by_from_model(cls, v, info):
        """Get created_by object from the model's created_by relationship."""
        if hasattr(info.data, "created_by") and info.data.created_by:
            return info.data.created_by
        return v

    model_config = {"from_attributes": True}
