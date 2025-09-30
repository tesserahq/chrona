from tessera_sdk.utils.auth import get_current_user
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.db import get_db
from app.schemas.author import (
    AuthorCreate,
    AuthorUpdate,
    AuthorMerge,
    Author,
)
from app.schemas.workspace import Workspace
from app.services.author_service import AuthorService
from app.models.author import Author as AuthorModel
from app.routers.utils.dependencies import get_author_by_id, get_workspace_by_id

# Workspace-scoped router for list and create operations
workspace_router = APIRouter(
    prefix="/workspaces/{workspace_id}/authors", tags=["authors"]
)

# Global router for individual author operations
router = APIRouter(prefix="/authors", tags=["authors"])


# Workspace-scoped endpoints
@workspace_router.get("", response_model=Page[Author])
def list_authors(
    workspace: Workspace = Depends(get_workspace_by_id),
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all authors in a workspace with pagination."""
    # Validate workspace access

    service = AuthorService(db)
    query = service.get_authors_by_workspace_query(workspace.id)
    return paginate(query, params)


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


@workspace_router.post("/merge", response_model=dict, status_code=status.HTTP_200_OK)
def merge_authors(
    merge_request: AuthorMerge,
    workspace: Workspace = Depends(get_workspace_by_id),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Merge multiple authors into a single author within a workspace.

    This endpoint:
    - Validates workspace access through the URL path
    - Validates that all authors exist and belong to the specified workspace
    - Updates all source_author records to point to the merge_to author
    - Soft deletes the original authors
    - Returns the updated target author
    """
    service = AuthorService(db)

    # Additional validation: ensure all authors belong to the specified workspace
    target_author = service.get_author(merge_request.merge_to_author_id)
    if not target_author or target_author.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target author not found in this workspace",
        )

    for author_id in merge_request.author_ids:
        author = service.get_author(author_id)
        if not author or author.workspace_id != workspace.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Author {author_id} not found in this workspace",
            )

    try:
        success = service.merge_authors(
            author_ids=merge_request.author_ids,
            merge_to_author_id=merge_request.merge_to_author_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to merge authors",
            )

        # Return the updated target author
        target_author = service.get_author(merge_request.merge_to_author_id)
        if not target_author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target author not found after merge",
            )

        return {
            "data": Author.model_validate(target_author),
            "message": f"Successfully merged {len(merge_request.author_ids)} authors into target author",
            "merged_author_ids": merge_request.author_ids,
            "target_author_id": merge_request.merge_to_author_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during merge: {str(e)}",
        )


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

    updated = service.update_author(UUID(str(author.id)), author_update)
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

    success = service.delete_author(UUID(str(author.id)))
    if not success:
        raise HTTPException(status_code=404, detail="Author not found")
    return {"message": "Author deleted successfully"}


# Moved to workspace-scoped router below
