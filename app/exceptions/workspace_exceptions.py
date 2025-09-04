"""Workspace-related exceptions."""


class WorkspaceLockedError(Exception):
    """Raised when trying to delete a locked workspace."""

    def __init__(self, workspace_id: str):
        self.message = f"Workspace {workspace_id} is locked and cannot be deleted. Unlock it first."
        super().__init__(self.message)
        self.workspace_id = workspace_id
