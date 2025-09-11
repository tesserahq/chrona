from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.import_request_item import ImportRequestItem
from app.schemas.project_import import ImportItemData
from app.schemas.author import AuthorCreate
from app.schemas.entry import EntryCreate
from app.schemas.entry_update import EntryUpdateCreate
from app.schemas.import_request_item import ImportRequestItemUpdate
from app.services.author_service import AuthorService
from app.services.entry_service import EntryService
from app.services.entry_update_service import EntryUpdateService
from app.services.source_author_service import SourceAuthorService
from app.services.import_request_service import ImportRequestService
from app.constants.import_constants import ImportItemStatuses


class ProcessImportItemCommand:
    """Command to process a single import item and create associated entities."""

    def __init__(self, db: Session):
        self.db = db
        self.author_service = AuthorService(db)
        self.entry_service = EntryService(db)
        self.entry_update_service = EntryUpdateService(db)
        self.source_author_service = SourceAuthorService(db)
        self.import_request_service = ImportRequestService(db)

    def execute(
        self,
        import_request_item: ImportRequestItem,
        project: Project,
    ) -> Dict[str, Any]:
        """
        Process a single import item and create authors, entries, entry_updates, etc.

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

            # Create entry updates if any
            entry_updates = self._create_entry_updates(
                item_data, entry.id, project.workspace_id, import_request_item.source_id
            )

            # Update the import request item status
            update_data = ImportRequestItemUpdate(
                status=ImportItemStatuses.SUCCESS,
                raw_payload={
                    **import_request_item.raw_payload,
                    "created_author_id": str(author.id),
                    "created_entry_id": str(entry.id),
                    "created_entry_update_ids": [str(entry_update.id) for entry_update in entry_updates],
                },
            )
            self.import_request_service.update_import_request_item(
                import_request_item.id, update_data
            )

            return {
                "success": True,
                "author_id": author.id,
                "entry_id": entry.id,
                "entry_update_ids": [entry_update.id for entry_update in entry_updates],
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
        """Create an entry from the item data, or update existing one if it already exists."""
        # Check if entry already exists
        existing_entry = self.entry_service.get_entry_by_external_id(
            source_id, external_id
        )

        if existing_entry:
            # Update existing entry with new data
            from app.schemas.entry import EntryUpdate

            entry_update = EntryUpdate(
                title=item_data.title,
                body=item_data.body,
                tags=item_data.tags,
                labels=item_data.labels,
                meta_data=item_data.meta_data,
            )
            return self.entry_service.update_entry(existing_entry.id, entry_update)

        # Create new entry
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

    def _create_entry_updates(
        self,
        item_data: ImportItemData,
        entry_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
    ):
        """Create entry updates from the item data entry_updates field, or update existing ones if they already exist."""
        entry_updates = []

        if not item_data.entry_updates:
            return entry_updates

        for updates in item_data.entry_updates:
            entry_update = self._process_single_entry_update(
                updates, entry_id, workspace_id, source_id
            )
            entry_updates.append(entry_update)

        return entry_updates

    def _process_single_entry_update(
        self,
        updates,
        entry_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
    ):
        """Process a single entry update - either update existing or create new."""
        existing_entry_update = self.entry_update_service.get_entry_update_by_external_id(
            source_id, updates.id
        )

        if existing_entry_update:
            return self._update_existing_entry_update(existing_entry_update, updates)
        else:
            return self._create_new_entry_update(
                updates, entry_id, workspace_id, source_id
            )

    def _update_existing_entry_update(self, existing_entry_update, updates):
        """Update an existing entry update with new data."""
        from app.schemas.entry_update import EntryUpdateUpdate

        entry_update_update = EntryUpdateUpdate(
            body=updates.body,
            tags=updates.tags,
            labels=updates.labels,
            meta_data=self._extract_update_meta_data(updates),
        )

        return self.entry_update_service.update_entry_update(existing_entry_update.id, entry_update_update)

    def _create_new_entry_update(
        self,
        updates,
        entry_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
    ):
        """Create a new entry update with author and source author relationships."""
        # Create or get the entry update author
        entry_update_author = self._create_or_get_author(updates.author, workspace_id)

        # Create or get the source author relationship for the entry update author
        source_author = self._create_or_get_source_author(
            entry_update_author.id, source_id, updates.author.id
        )

        entry_update_create = EntryUpdateCreate(
            body=updates.body,
            source_author_id=source_author.id,
            entry_id=entry_id,
            tags=updates.tags,
            labels=updates.labels,
            meta_data=self._extract_update_meta_data(updates),
            external_id=updates.id,
            source_id=source_id,
        )

        return self.entry_update_service.create_entry_update(entry_update_create)

    def _extract_update_meta_data(self, updates):
        """Extract meta_data from updates, handling missing attribute gracefully."""
        return updates.meta_data if hasattr(updates, "meta_data") else {}
