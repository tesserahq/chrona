from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.models.import_request import ImportRequest
from app.models.import_request_item import ImportRequestItem
from app.schemas.import_request import (
    ImportRequestCreate,
    ImportRequestUpdate,
)
from app.schemas.import_request_item import (
    ImportRequestItemCreate,
    ImportRequestItemUpdate,
)

from app.utils.db.filtering import apply_filters
from app.services.soft_delete_service import SoftDeleteService

"""
Module providing the ImportRequestService class for managing ImportRequest entities.
Includes methods for CRUD operations and dynamic searching with flexible filters.
"""


class ImportRequestService(SoftDeleteService[ImportRequest]):
    def __init__(self, db: Session):
        super().__init__(db, ImportRequest)

    def get_import_request(self, import_request_id: UUID) -> Optional[ImportRequest]:
        """Get a single import request by ID."""
        return (
            self.db.query(ImportRequest)
            .options(joinedload(ImportRequest.source), joinedload(ImportRequest.user))
            .filter(ImportRequest.id == import_request_id)
            .first()
        )

    def get_import_requests(
        self, skip: int = 0, limit: int = 100
    ) -> List[ImportRequest]:
        """Get a list of import requests with pagination."""
        return self.db.query(ImportRequest).offset(skip).limit(limit).all()

    def get_import_requests_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ImportRequest]:
        """Get import requests for a specific project."""
        return (
            self.db.query(ImportRequest)
            .filter(ImportRequest.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_import_requests_by_project_query(self, project_id: UUID):
        """Get a query object for import requests by project for use with fastapi-pagination."""
        return (
            self.db.query(ImportRequest)
            .options(joinedload(ImportRequest.source), joinedload(ImportRequest.user))
            .filter(ImportRequest.project_id == project_id)
        )

    def get_import_requests_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ImportRequest]:
        """Get import requests requested by a specific user."""
        return (
            self.db.query(ImportRequest)
            .filter(ImportRequest.requested_by_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_import_request(
        self, import_request: ImportRequestCreate
    ) -> ImportRequest:
        """Create a new import request."""
        db_import_request = ImportRequest(**import_request.model_dump())
        self.db.add(db_import_request)
        self.db.commit()
        self.db.refresh(db_import_request)
        return db_import_request

    def update_import_request(
        self, import_request_id: UUID, import_request: ImportRequestUpdate
    ) -> Optional[ImportRequest]:
        """Update an existing import request."""
        db_import_request = (
            self.db.query(ImportRequest)
            .filter(ImportRequest.id == import_request_id)
            .first()
        )
        if db_import_request:
            update_data = import_request.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_import_request, key, value)
            self.db.commit()
            self.db.refresh(db_import_request)
        return db_import_request

    def delete_import_request(self, import_request_id: UUID) -> bool:
        """Soft delete an import request."""
        return self.delete_record(import_request_id)

    def search(self, filters: Dict[str, Any]) -> List[ImportRequest]:
        """
        Search import requests based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%pending%"}

        Returns:
            List[ImportRequest]: List of import requests matching the filter criteria.

        Example:
            filters = {
                "status": {"operator": "ilike", "value": "%pending%"},
                "source": "csv",
                "project_id": {"operator": "=", "value": "123e4567-e89b-12d3-a456-426614174000"}
            }
        """
        query = self.db.query(ImportRequest)
        query = apply_filters(query, ImportRequest, filters)
        return query.all()

    def search_query(self, filters: Dict[str, Any]):
        """Get a query object for import request search for use with fastapi-pagination."""
        query = self.db.query(ImportRequest).options(
            joinedload(ImportRequest.source), joinedload(ImportRequest.user)
        )
        query = apply_filters(query, ImportRequest, filters)
        return query

    def get_import_request_items(
        self, import_request_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ImportRequestItem]:
        """Get all items for a specific import request."""
        return (
            self.db.query(ImportRequestItem)
            .filter(ImportRequestItem.import_request_id == import_request_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_import_request_item(
        self, import_request_item: ImportRequestItemCreate
    ) -> ImportRequestItem:
        """Create a new import request item."""
        db_import_request_item = ImportRequestItem(**import_request_item.model_dump())
        self.db.add(db_import_request_item)
        self.db.commit()
        self.db.refresh(db_import_request_item)
        return db_import_request_item

    def update_import_request_item(
        self, item_id: UUID, import_request_item: ImportRequestItemUpdate
    ) -> Optional[ImportRequestItem]:
        """Update an existing import request item."""
        db_import_request_item = (
            self.db.query(ImportRequestItem)
            .filter(ImportRequestItem.id == item_id)
            .first()
        )
        if db_import_request_item:
            update_data = import_request_item.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_import_request_item, key, value)
            self.db.commit()
            self.db.refresh(db_import_request_item)
        return db_import_request_item

    def delete_import_request_item(self, item_id: UUID) -> bool:
        """Soft delete an import request item."""
        item = (
            self.db.query(ImportRequestItem)
            .filter(ImportRequestItem.id == item_id)
            .first()
        )
        if item:
            item.deleted_at = self._get_current_timestamp()
            self.db.commit()
            return True
        return False

    def search_items(self, filters: Dict[str, Any]) -> List[ImportRequestItem]:
        """
        Search import request items based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%success%"}

        Returns:
            List[ImportRequestItem]: List of import request items matching the filter criteria.
        """
        query = self.db.query(ImportRequestItem)
        query = apply_filters(query, ImportRequestItem, filters)
        return query.all()

    def get_import_request_stats(
        self, import_request_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get statistics for an import request."""
        import_request = self.get_import_request(import_request_id)
        if not import_request:
            return None

        # Get item counts by status
        items = self.get_import_request_items(import_request_id, skip=0, limit=1000)
        status_counts = {}
        for item in items:
            status = item.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "import_request_id": import_request_id,
            "total_items": len(items),
            "status_counts": status_counts,
            "received_count": import_request.received_count,
            "success_count": import_request.success_count,
            "failure_count": import_request.failure_count,
            "completion_rate": (
                (import_request.success_count / import_request.received_count * 100)
                if import_request.received_count > 0
                else 0
            ),
        }

    def _get_current_timestamp(self):
        """Get current timestamp for soft delete operations."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc)
