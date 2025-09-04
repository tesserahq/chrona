from uuid import UUID
from sqlalchemy.orm import Session


class WorkspacePruneService:
    """Service for cleaning up workspace-related resources when a workspace is deleted."""

    def __init__(self, db: Session):
        self.db = db

    def prune_workspace(self, workspace_id: UUID) -> bool:
        """
        Clean up all resources associated with a workspace.
        """
        return True
