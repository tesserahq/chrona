from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from app.schemas.user import User
else:
    from app.schemas.user import User


class ProjectMembershipBase(BaseModel):
    user_id: UUID
    project_id: UUID
    role: str
    created_by_id: UUID


class ProjectMembershipCreate(ProjectMembershipBase):
    pass


class ProjectMembershipUpdate(BaseModel):
    role: Optional[str] = None


class ProjectMembershipInDB(ProjectMembershipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMembershipResponse(ProjectMembershipBase):
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

    class Config:
        from_attributes = True
