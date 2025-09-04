from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from uuid import UUID
from pydantic import BaseModel, field_validator, EmailStr
from app.constants.membership import MembershipRoles

if TYPE_CHECKING:
    from app.schemas.user import User
    from app.schemas.workspace import Workspace
else:
    from app.schemas.user import User
    from app.schemas.workspace import Workspace


class ProjectAssignment(BaseModel):
    id: UUID
    role: str


class InvitationBase(BaseModel):
    email: EmailStr
    role: str = MembershipRoles.COLLABORATOR
    message: Optional[str] = None
    projects: Optional[List[ProjectAssignment]] = None


class InvitationCreate(InvitationBase):
    workspace_id: UUID
    inviter_id: UUID


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: str = MembershipRoles.COLLABORATOR
    message: Optional[str] = None
    projects: Optional[List[ProjectAssignment]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in [
            MembershipRoles.OWNER,
            MembershipRoles.COLLABORATOR,
            MembershipRoles.ADMIN,
            MembershipRoles.PROJECT_MEMBER,
        ]:
            raise ValueError(
                f"Invalid membership type. Must be one of: {MembershipRoles.OWNER}, {MembershipRoles.COLLABORATOR}, {MembershipRoles.ADMIN}, {MembershipRoles.PROJECT_MEMBER}"
            )
        return v


class InvitationUpdate(BaseModel):
    message: Optional[str] = None
    role: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in [
            MembershipRoles.OWNER,
            MembershipRoles.COLLABORATOR,
            MembershipRoles.ADMIN,
            MembershipRoles.PROJECT_MEMBER,
        ]:
            raise ValueError(
                f"Invalid membership type. Must be one of: {MembershipRoles.OWNER}, {MembershipRoles.COLLABORATOR}, {MembershipRoles.ADMIN}, {MembershipRoles.PROJECT_MEMBER}"
            )
        return v


class InvitationResponse(InvitationBase):
    id: UUID
    workspace_id: UUID
    inviter_id: UUID
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    workspace: Optional[Workspace] = None
    inviter: Optional[User] = None

    @field_validator("workspace", mode="before")
    @classmethod
    def get_workspace_from_model(cls, v, info):
        """Get workspace object from the model's workspace relationship."""
        if hasattr(info.data, "workspace") and info.data.workspace:
            return info.data.workspace
        return v

    @field_validator("inviter", mode="before")
    @classmethod
    def get_inviter_from_model(cls, v, info):
        """Get inviter object from the model's inviter relationship."""
        if hasattr(info.data, "inviter") and info.data.inviter:
            return info.data.inviter
        return v

    class Config:
        from_attributes = True
