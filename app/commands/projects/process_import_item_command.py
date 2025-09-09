from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.import_request_item import ImportRequestItem
from app.schemas.project_import import ImportItemData
from app.schemas.author import AuthorCreate
from app.schemas.entry import EntryCreate
from app.schemas.comment import CommentCreate
from app.schemas.source_author import SourceAuthorCreate
from app.schemas.import_request_item import ImportRequestItemUpdate
from app.services.author_service import AuthorService
from app.services.entry_service import EntryService
from app.services.comment_service import CommentService
from app.services.source_author_service import SourceAuthorService
from app.services.import_request_service import ImportRequestService
from app.constants.import_constants import ImportItemStatuses


class ProcessImportItemCommand:
    """Command to process a single import item and create associated entities."""

    def __init__(self, db: Session):
        self.db = db
        self.author_service = AuthorService(db)
        self.entry_service = EntryService(db)
        self.comment_service = CommentService(db)
        self.source_author_service = SourceAuthorService(db)
        self.import_request_service = ImportRequestService(db)

    def execute(
        self,
        import_request_item: ImportRequestItem,
        project: Project,
    ) -> Dict[str, Any]:
        """
        Process a single import item and create authors, entries, comments, etc.

        :param import_request_item: The import request item to process
        :param project: The project to create entities in
        :return: Dictionary with processing results
        """
        try:
            # Extract the item data from the raw payload
            item_data = ImportItemData.model_validate(import_request_item.raw_payload)

            # Create or get the author
            author = self._create_or_get_author(item_data.author, project.workspace_id)

            # Create or get the source author relationship
            source_author = self._create_or_get_source_author(
                author.id, import_request_item.source_id, item_data.author.id
            )

            # Create the entry
            entry = self._create_entry(
                item_data,
                source_author.id,
                import_request_item.source_id,
                project.id,
                import_request_item.source_item_id,
            )

            # Create comments if any
            comments = self._create_comments(
                item_data, entry.id, project.workspace_id, import_request_item.source_id
            )

            # Update the import request item status
            update_data = ImportRequestItemUpdate(
                status=ImportItemStatuses.SUCCESS,
                raw_payload={
                    **import_request_item.raw_payload,
                    "created_author_id": str(author.id),
                    "created_entry_id": str(entry.id),
                    "created_comment_ids": [str(comment.id) for comment in comments],
                },
            )
            self.import_request_service.update_import_request_item(
                import_request_item.id, update_data
            )

            return {
                "success": True,
                "author_id": author.id,
                "entry_id": entry.id,
                "comment_ids": [comment.id for comment in comments],
                "source_author_id": source_author.id,
            }

        except Exception as e:
            # Update the import request item status to failed
            update_data = ImportRequestItemUpdate(
                status=ImportItemStatuses.FAILED,
                raw_payload={
                    **import_request_item.raw_payload,
                    "error": str(e),
                },
            )
            self.import_request_service.update_import_request_item(
                import_request_item.id, update_data
            )

            return {
                "success": False,
                "error": str(e),
            }

    def _create_or_get_author(self, author_data, workspace_id: UUID):
        """Create or get an existing author."""
        # Check if author already exists by email in this workspace
        existing_authors = self.author_service.get_authors_by_workspace(workspace_id)
        for existing_author in existing_authors:
            if existing_author.email == author_data.email:
                return existing_author

        # Create new author
        author_create = AuthorCreate(
            display_name=author_data.display_name,
            avatar_url=author_data.avatar_url,
            email=author_data.email,
            tags=author_data.tags,
            labels=author_data.labels,
            meta_data=author_data.meta_data,
        )

        return self.author_service.create_author(author_create, workspace_id)

    def _create_or_get_source_author(
        self, author_id: UUID, source_id: UUID, source_author_id: str
    ):
        """Create or get a source author relationship."""
        return self.source_author_service.get_or_create_source_author(
            source_id, author_id, source_author_id
        )

    def _create_entry(
        self,
        item_data: ImportItemData,
        source_author_id: UUID,
        source_id: UUID,
        project_id: UUID,
        external_id: str,
    ):
        """Create an entry from the item data."""
        entry_create = EntryCreate(
            title=item_data.title,
            body=item_data.body,
            source_id=source_id,
            external_id=external_id,
            tags=item_data.tags,
            labels=item_data.labels,
            meta_data=item_data.meta_data,
            source_author_id=source_author_id,
            project_id=project_id,
        )

        return self.entry_service.create_entry(entry_create)

    def _create_comments(
        self,
        item_data: ImportItemData,
        entry_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
    ):
        """Create comments from the item data comments field."""
        comments = []

        # Only create comments if the comments field is present and not empty
        if item_data.comments:
            for comment_data in item_data.comments:
                # Create or get the comment author
                comment_author = self._create_or_get_author(
                    comment_data.author, workspace_id
                )

                # Create or get the source author relationship for the comment author
                source_author = self._create_or_get_source_author(
                    comment_author.id, source_id, comment_data.author.id
                )

                comment_create = CommentCreate(
                    body=comment_data.body,
                    source_author_id=source_author.id,
                    entry_id=entry_id,
                    tags=comment_data.tags,
                    labels=comment_data.labels,
                    meta_data=(
                        comment_data.meta_data
                        if hasattr(comment_data, "meta_data")
                        else {}
                    ),
                    external_id=comment_data.id,
                    source_id=source_id,
                )

                comment = self.comment_service.create_comment(comment_create)
                comments.append(comment)

        return comments
