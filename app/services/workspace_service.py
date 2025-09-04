from typing import List, Optional, Dict, Any, cast
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from app.models.membership import Membership
from app.models.workspace import Workspace
from app.models.project import Project
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceStats,
    ProjectStats,
    ProjectSummary,
)
from app.utils.db.filtering import apply_filters
from app.services.workspace_prune_service import WorkspacePruneService
from app.services.soft_delete_service import SoftDeleteService
from app.exceptions.workspace_exceptions import WorkspaceLockedError
from app.services.membership_service import MembershipService

"""
Module providing the WorkspaceService class for managing Workspace entities.
Includes methods for CRUD operations and dynamic searching with flexible filters.
"""


class WorkspaceService(SoftDeleteService[Workspace]):
    def __init__(self, db: Session):
        super().__init__(db, Workspace)
        self.prune_service = WorkspacePruneService(db)

    def get_workspace(self, workspace_id: UUID) -> Optional[Workspace]:
        return self.db.query(Workspace).filter(Workspace.id == workspace_id).first()

    def get_workspaces_by_user_memberships(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Workspace]:
        """
        Get accounts that a user has access to based on their memberships.

        Args:
            user_id: The UUID of the user
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List[Account]: List of accounts the user has access to through memberships
        """
        query = (
            self.db.query(Workspace)
            .join(Membership, Workspace.id == Membership.workspace_id)
            .filter(
                Membership.user_id == user_id,
            )
            .offset(skip)
            .limit(limit)
        )
        return query.all()

    def get_workspaces(self, skip: int = 0, limit: int = 100) -> List[Workspace]:
        return self.db.query(Workspace).offset(skip).limit(limit).all()

    def create_workspace(self, workspace: WorkspaceCreate) -> Workspace:
        db_workspace = Workspace(**workspace.model_dump())
        self.db.add(db_workspace)
        self.db.commit()
        self.db.refresh(db_workspace)
        return db_workspace

    def update_workspace(
        self, workspace_id: UUID, workspace: WorkspaceUpdate
    ) -> Optional[Workspace]:
        db_workspace = (
            self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        )
        if db_workspace:
            update_data = workspace.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_workspace, key, value)
            self.db.commit()
            self.db.refresh(db_workspace)
        return db_workspace

    def delete_workspace(self, workspace_id: UUID) -> bool:
        """Soft delete a workspace after pruning its resources."""
        # First check if workspace exists and is not locked
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False

        if workspace.locked:
            raise WorkspaceLockedError(str(workspace_id))

        # First prune all workspace resources
        if not self.prune_service.prune_workspace(workspace_id):
            return False

        # Then soft delete the workspace
        return self.delete_record(workspace_id)

    def search(self, filters: Dict[str, Any]) -> List[Workspace]:
        """
        Search workspaces based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%john%"}

        Returns:
            List[Workspace]: List of workspaces matching the filter criteria.

        Example:
            filters = {
                "name": {"operator": "ilike", "value": "%john%"},
                "email": {"operator": "!=", "value": "test@example.com"},
                "is_active": True,
                "role": {"operator": "in", "value": ["admin", "user"]}
            }
        """
        query = self.db.query(Workspace)
        query = apply_filters(query, Workspace, filters)
        return query.all()

    def get_workspace_stats(self, workspace_id: UUID) -> Optional[WorkspaceStats]:
        """
        Get comprehensive statistics for a workspace with optimized queries.

        Returns:
            WorkspaceStats: Statistics for the workspace or None if workspace doesn't exist
        """
        # First verify the workspace exists
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None

        # Count total projects
        total_projects = (
            self.db.query(func.count(Project.id))
            .filter(Project.workspace_id == workspace_id)
            .scalar()
        )

        # Get 5 most recently updated projects
        recent_projects_query = (
            self.db.query(Project)
            .filter(Project.workspace_id == workspace_id)
            .order_by(desc(Project.updated_at))
            .limit(5)
        )
        recent_projects = [
            ProjectSummary(
                id=cast(UUID, p.id),
                name=cast(str, p.name),
                description=cast(Optional[str], p.description),
                updated_at=cast(datetime, p.updated_at),
            )
            for p in recent_projects_query.all()
        ]

        # Create project stats
        project_stats = ProjectStats(
            total_projects=total_projects or 0,
            recent_projects=recent_projects,
        )

        return WorkspaceStats(
            project_stats=project_stats,
        )

    def get_workspace_stats_for_user(
        self, workspace_id: UUID, user_id: UUID
    ) -> Optional[WorkspaceStats]:
        """
        Get workspace statistics filtered by the requesting user's accessible projects.
        Other stats (prompts, plugins, credentials) are counted at the workspace level.
        """
        # Verify workspace exists
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None

        membership_service = MembershipService(self.db)
        accessible_projects = membership_service.get_accessible_projects_for_user(
            workspace_id, user_id
        )
        accessible_project_ids = [p.id for p in accessible_projects]

        # Project stats filtered by access
        total_projects = len(accessible_project_ids)
        if total_projects == 0:
            recent_projects = []
        else:
            recent_projects_query = (
                self.db.query(Project)
                .filter(Project.id.in_(accessible_project_ids))
                .order_by(desc(Project.updated_at))
                .limit(5)
            )
            recent_projects = [
                ProjectSummary(
                    id=cast(UUID, p.id),
                    name=cast(str, p.name),
                    description=cast(Optional[str], p.description),
                    updated_at=cast(datetime, p.updated_at),
                )
                for p in recent_projects_query.all()
            ]

        project_stats = ProjectStats(
            total_projects=total_projects or 0, recent_projects=recent_projects
        )

        return WorkspaceStats(
            project_stats=project_stats,
        )
