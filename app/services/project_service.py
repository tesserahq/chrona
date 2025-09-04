from typing import List, Optional, Dict, Any
from uuid import UUID
from app.exceptions.resource_not_found_error import ResourceNotFoundError
from sqlalchemy.orm import Session
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, Project as ProjectSchema
from app.services.workspace_service import WorkspaceService
from app.utils.db.filtering import apply_filters
from app.services.soft_delete_service import SoftDeleteService


class ProjectService(SoftDeleteService[Project]):
    def __init__(self, db: Session):
        super().__init__(db, Project)
        self.workspace_service = WorkspaceService(db)

    def get_project(self, project_id: UUID) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        return self.db.query(Project).offset(skip).limit(limit).all()

    def create_project(self, project: ProjectCreate) -> Project:
        # Validate workspace exists
        if project.workspace_id:
            workspace = self.workspace_service.get_workspace(project.workspace_id)
            if not workspace:
                raise ResourceNotFoundError(
                    f"Workspace with ID {project.workspace_id} not found"
                )

        data = project.model_dump()

        db_project = Project(**data)
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)

        return db_project

    def update_project(
        self, project_id: UUID, project: ProjectUpdate
    ) -> Optional[Project]:
        db_project = self.db.query(Project).filter(Project.id == project_id).first()
        if db_project:
            update_data = project.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_project, key, value)
            self.db.commit()
            self.db.refresh(db_project)
        return db_project

    def delete_project(self, project_id: UUID) -> bool:
        """Soft delete a project and drop its vector index table."""
        db_project = self.db.query(Project).filter(Project.id == project_id).first()
        if db_project:
            # Then soft delete the project
            return self.delete_record(project_id)
        return False

    # moved to NodeService

    def search(self, filters: Dict[str, Any]) -> List[ProjectSchema]:
        """
        Search projects based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%john%"}

        Returns:
            List[ProjectSchema]: List of projects matching the filter criteria.
        """
        query = self.db.query(Project)
        query = apply_filters(query, Project, filters)
        return [ProjectSchema.model_validate(project) for project in query.all()]
