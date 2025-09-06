from app.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from typing import List

from app.db import get_db
from app.schemas.author import (
    AuthorCreate,
    AuthorUpdate,
    Author,
)
from app.schemas.workspace import Workspace
from app.services.author_service import AuthorService
from app.models.author import Author as AuthorModel
from app.schemas.common import ListResponse
from app.routers.utils.dependencies import get_author_by_id, get_workspace_by_id

# Workspace-scoped router for list and create operations
workspace_router = APIRouter(
    prefix="/workspaces/{workspace_id}/authors", tags=["authors"]
)

# Global router for individual author operations
router = APIRouter(prefix="/authors", tags=["authors"])


# Workspace-scoped endpoints
@workspace_router.get("", response_model=ListResponse[Author])
def list_authors(
    workspace: Workspace = Depends(get_workspace_by_id),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all authors in a workspace with pagination."""
    # Validate workspace access

    service = AuthorService(db)
    authors = service.get_authors_by_workspace(workspace.id, skip, limit)
    return ListResponse(data=authors)


@workspace_router.post("", response_model=Author, status_code=status.HTTP_201_CREATED)
def create_author(
    author: AuthorCreate,
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new author in a workspace."""
    # Validate workspace access

    service = AuthorService(db)
    return service.create_author(author, workspace_id=workspace.id)


# Global author endpoints
@router.get("/{author_id}", response_model=Author)
def get_author(
    author: AuthorModel = Depends(get_author_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific author by ID."""
    service = AuthorService(db)

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    return author


@router.put("/{author_id}", response_model=Author)
def update_author(
    author_update: AuthorUpdate,
    author: AuthorModel = Depends(get_author_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing author."""
    service = AuthorService(db)

    updated = service.update_author(author.id, author_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return updated


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(
    author: AuthorModel = Depends(get_author_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an author."""
    service = AuthorService(db)

    success = service.delete_author(author.id)
    if not success:
        raise HTTPException(status_code=404, detail="Author not found")
    return {"message": "Author deleted successfully"}
