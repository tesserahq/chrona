from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.project_membership import ProjectMembership
from app.schemas.project_membership import (
    ProjectMembershipCreate,
    ProjectMembershipUpdate,
)
from app.utils.db.filtering import apply_filters
from app.services.soft_delete_service import SoftDeleteService


class ProjectMembershipService(SoftDeleteService[ProjectMembership]):
    def __init__(self, db: Session):
        super().__init__(db, ProjectMembership)

    def get_project_membership(
        self, membership_id: UUID
    ) -> Optional[ProjectMembership]:
        return (
            self.db.query(ProjectMembership)
            .options(
                joinedload(ProjectMembership.user),
                joinedload(ProjectMembership.project),
            )
            .filter(ProjectMembership.id == membership_id)
            .first()
        )

    def get_project_memberships(
        self, skip: int = 0, limit: int = 100
    ) -> List[ProjectMembership]:
        return self.db.query(ProjectMembership).offset(skip).limit(limit).all()

    def get_memberships_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ProjectMembership]:
        return (
            self.db.query(ProjectMembership)
            .options(joinedload(ProjectMembership.project))
            .filter(ProjectMembership.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_memberships_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ProjectMembership]:
        return (
            self.db.query(ProjectMembership)
            .options(
                joinedload(ProjectMembership.user),
                joinedload(ProjectMembership.created_by),
            )
            .filter(ProjectMembership.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_project_membership(
        self, user_id: UUID, project_id: UUID
    ) -> Optional[ProjectMembership]:
        return (
            self.db.query(ProjectMembership)
            .filter(
                and_(
                    ProjectMembership.user_id == user_id,
                    ProjectMembership.project_id == project_id,
                )
            )
            .first()
        )

    def create_project_membership(
        self, membership: ProjectMembershipCreate
    ) -> ProjectMembership:
        db_membership = ProjectMembership(**membership.model_dump())
        self.db.add(db_membership)
        self.db.commit()
        self.db.refresh(db_membership)
        return db_membership

    def update_project_membership(
        self, membership_id: UUID, membership: ProjectMembershipUpdate
    ) -> Optional[ProjectMembership]:
        db_membership = (
            self.db.query(ProjectMembership)
            .filter(ProjectMembership.id == membership_id)
            .first()
        )
        if db_membership:
            update_data = membership.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_membership, key, value)
            self.db.commit()
            self.db.refresh(db_membership)
        return db_membership

    def delete_project_membership(self, membership_id: UUID) -> bool:
        return self.delete_record(membership_id)

    def search(self, filters: Dict[str, Any]) -> List[ProjectMembership]:
        query = self.db.query(ProjectMembership)
        query = apply_filters(query, ProjectMembership, filters)
        return query.all()
