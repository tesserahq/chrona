from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.constants.membership import MembershipRoles
from app.models.membership import Membership
from app.schemas.membership import MembershipCreate, MembershipUpdate
from app.utils.db.filtering import apply_filters
from app.services.soft_delete_service import SoftDeleteService
from app.models.project import Project
from app.models.project_membership import ProjectMembership

"""
Module providing the MembershipService class for managing Membership entities.
Includes methods for CRUD operations, role management, and workspace membership queries.
"""


class MembershipService(SoftDeleteService[Membership]):
    def __init__(self, db: Session):
        super().__init__(db, Membership)

    def get_memberships_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Membership]:
        """Get memberships for a specific user."""
        query = (
            self.db.query(Membership)
            .options(
                joinedload(Membership.workspace), joinedload(Membership.created_by)
            )
            .filter(Membership.user_id == user_id)
        )
        return query.offset(skip).limit(limit).all()

    def get_membership(self, membership_id: UUID) -> Optional[Membership]:
        """Get a membership by its ID."""
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.created_by))
            .filter(Membership.id == membership_id)
            .first()
        )

    def get_user_memberships(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Membership]:
        """Get all memberships for a specific user."""
        return (
            self.db.query(Membership)
            .filter(Membership.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_memberships_by_workspace(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Membership]:
        """Get all memberships for a specific workspace."""
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.created_by))
            .filter(Membership.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_workspace_membership(
        self, user_id: UUID, workspace_id: UUID
    ) -> Optional[Membership]:
        """Get a specific user's membership in a workspace."""
        return (
            self.db.query(Membership)
            .filter(
                and_(
                    Membership.user_id == user_id,
                    Membership.workspace_id == workspace_id,
                )
            )
            .first()
        )

    def create_membership(self, membership: MembershipCreate) -> Membership:
        """Create a new membership."""
        db_membership = Membership(**membership.model_dump())
        self.db.add(db_membership)
        self.db.commit()
        self.db.refresh(db_membership)
        return db_membership

    def update_membership(
        self, membership_id: UUID, membership: MembershipUpdate
    ) -> Optional[Membership]:
        """Update a membership's role."""
        db_membership = (
            self.db.query(Membership).filter(Membership.id == membership_id).first()
        )
        if db_membership:
            update_data = membership.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_membership, key, value)
            self.db.commit()
            self.db.refresh(db_membership)
        return db_membership

    def delete_membership(self, membership_id: UUID) -> bool:
        """Soft delete a membership."""
        return self.delete_record(membership_id)

    def search(self, filters: Dict[str, Any]) -> List[Membership]:
        """
        Search memberships based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%admin%"}

        Returns:
            List[Membership]: List of memberships matching the filter criteria.

        Example:
            filters = {
                "role": {"operator": "in", "value": ["admin", "owner"]},
                "workspace_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        """
        query = self.db.query(Membership)
        query = apply_filters(query, Membership, filters)
        return query.all()

    def get_active_owners_count(self, workspace_id: UUID) -> int:
        """Get the count of active owner memberships for an account."""
        return (
            self.db.query(Membership)
            .filter(
                and_(
                    Membership.workspace_id == workspace_id,
                    Membership.role == MembershipRoles.OWNER,
                )
            )
            .count()
        )

    def get_accessible_projects_for_user(
        self, workspace_id: UUID, user_id: UUID
    ) -> List[Project]:
        """Return projects in a workspace that the user can access.

        - If the user has a workspace membership with role project_member,
          return only projects where the user has a project membership.
        - Otherwise, return all projects in the workspace.
        """
        membership = self.get_user_workspace_membership(user_id, workspace_id)
        if membership is None:
            return []

        if membership.role == MembershipRoles.PROJECT_MEMBER:
            return (
                self.db.query(Project)
                .join(
                    ProjectMembership,
                    ProjectMembership.project_id == Project.id,
                )
                .filter(
                    and_(
                        Project.workspace_id == workspace_id,
                        ProjectMembership.user_id == user_id,
                    )
                )
                .all()
            )

        # Owners/admins/collaborators: full access to workspace projects
        return self.db.query(Project).filter(Project.workspace_id == workspace_id).all()

    def validate_delete_membership_permissions(
        self, membership_id: UUID, current_user_id: UUID, workspace_id: UUID
    ) -> None:
        """
        Validate permissions for deleting a membership.

        Raises:
            HTTPException: If validation fails
        """
        # Get the membership to be deleted
        membership = self.get_membership(membership_id)
        if not membership:
            raise HTTPException(status_code=404, detail="Membership not found")

        # Get current user's membership in this account
        current_user_membership = self.get_user_workspace_membership(
            current_user_id, workspace_id
        )

        if not current_user_membership:
            raise HTTPException(
                status_code=403, detail="You don't have access to this account"
            )

        # Validation 1: Only owners can delete other owners
        if membership.is_owner() and not current_user_membership.is_owner():
            raise HTTPException(
                status_code=403, detail="Only owners can delete other owners"
            )

        # Validation 2: Users can't delete themselves
        if membership.user_id == current_user_id:
            raise HTTPException(
                status_code=400, detail="You cannot delete your own membership"
            )

        # Validation 3: At least one owner must exist in the workspace
        if membership.is_owner():
            active_owners_count = self.get_active_owners_count(workspace_id)
            if active_owners_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the last owner. At least one owner must remain in the workspace.",
                )

    def delete_membership_with_validation(
        self, membership_id: UUID, current_user_id: UUID, workspace_id: UUID
    ) -> bool:
        """
        Delete a membership with full validation.

        Args:
            membership_id: ID of the membership to delete
            current_user_id: ID of the user performing the deletion
            workspace_id: ID of the account the membership belongs to

        Returns:
            bool: True if deletion was successful

        Raises:
            HTTPException: If validation fails
        """
        # Validate permissions
        self.validate_delete_membership_permissions(
            membership_id, current_user_id, workspace_id
        )

        # Perform the deletion
        return self.delete_membership(membership_id)
