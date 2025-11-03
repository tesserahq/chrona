from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.entry import Entry
from app.models.source_author import SourceAuthor
from app.schemas.entry import EntryCreate, EntryUpdate
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class EntryService(SoftDeleteService[Entry]):
    def __init__(self, db: Session):
        super().__init__(db, Entry)

    def get_entry(self, entry_id: UUID) -> Optional[Entry]:
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.entry_updates),
            )
            .filter(Entry.id == entry_id)
            .first()
        )

    def get_entries(self, skip: int = 0, limit: int = 100) -> List[Entry]:
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.entry_updates),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_entries_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Entry]:
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.entry_updates),
            )
            .filter(Entry.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_entries_by_project_query(self, project_id: UUID):
        """Get a query object for entries by project for use with fastapi-pagination."""
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.entry_updates),
            )
            .filter(Entry.project_id == project_id)
            .order_by(Entry.source_created_at.desc())
        )

    def create_entry(self, entry: EntryCreate) -> Entry:
        db_entry = Entry(**entry.model_dump())
        self.db.add(db_entry)
        self.db.commit()
        self.db.refresh(db_entry)
        # Reload with source, source_author, and entry_updates relationships
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.entry_updates),
            )
            .filter(Entry.id == db_entry.id)
            .first()
        )

    def update_entry(self, entry_id: UUID, entry: EntryUpdate) -> Optional[Entry]:
        db_entry = self.db.query(Entry).filter(Entry.id == entry_id).first()
        if db_entry:
            update_data = entry.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_entry, key, value)
            self.db.commit()
            self.db.refresh(db_entry)
            # Reload with source, source_author, and entry_updates relationships
            return (
                self.db.query(Entry)
                .options(
                    joinedload(Entry.source),
                    joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                    selectinload(Entry.entry_updates),
                )
                .filter(Entry.id == entry_id)
                .first()
            )
        return db_entry

    def delete_entry(self, entry_id: UUID) -> bool:
        return self.delete_record(entry_id)

    def get_entry_by_external_id(
        self, source_id: UUID, external_id: str
    ) -> Optional[Entry]:
        """Get an entry by source ID and external ID."""
        return (
            self.db.query(Entry)
            .options(
                joinedload(Entry.source),
                joinedload(Entry.source_author).selectinload(SourceAuthor.author),
                selectinload(Entry.entry_updates),
            )
            .filter(
                Entry.source_id == source_id,
                Entry.external_id == external_id,
            )
            .first()
        )

    def _process_date_range_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process DateRangeFilter objects in filters dict and convert them to operator-based filters.

        Converts DateRangeFilter (with 'from' and 'to' keys) into >= and <= operator filters
        that apply_filters can handle.
        """
        processed_filters = filters.copy()

        # Check if created_at is a DateRangeFilter (dict with 'from'/'from_date' and 'to'/'to_date' keys)
        if "created_at" in processed_filters:
            created_at_filter = processed_filters.get("created_at")
            # Check if it's a dict (after model_dump) or has the DateRangeFilter structure
            if isinstance(created_at_filter, dict):
                # Check for both alias keys (from/to) and field name keys (from_date/to_date)
                has_from = (
                    "from" in created_at_filter or "from_date" in created_at_filter
                )
                has_to = "to" in created_at_filter or "to_date" in created_at_filter
                if has_from and has_to:
                    # It's a DateRangeFilter, extract dates (support both alias and field names)
                    from_date = created_at_filter.get("from") or created_at_filter.get(
                        "from_date"
                    )
                    to_date = created_at_filter.get("to") or created_at_filter.get(
                        "to_date"
                    )

                    # Remove the original created_at filter and we'll handle it separately
                    del processed_filters["created_at"]

                    # Store the date range info for later processing
                    processed_filters["_date_range_created_at"] = {
                        "from": from_date,
                        "to": to_date,
                    }
            # Also check if it's a Pydantic BaseModel instance (DateRangeFilter)
            elif hasattr(created_at_filter, "from_date") and hasattr(
                created_at_filter, "to_date"
            ):
                # It's a DateRangeFilter Pydantic model instance
                from_date = created_at_filter.from_date
                to_date = created_at_filter.to_date

                # Remove the original created_at filter and we'll handle it separately
                del processed_filters["created_at"]

                # Store the date range info for later processing
                processed_filters["_date_range_created_at"] = {
                    "from": from_date,
                    "to": to_date,
                }

        # Check if updated_at is a DateRangeFilter (dict with 'from'/'from_date' and 'to'/'to_date' keys)
        if "updated_at" in processed_filters:
            updated_at_filter = processed_filters.get("updated_at")
            # Check if it's a dict (after model_dump) or has the DateRangeFilter structure
            if isinstance(updated_at_filter, dict):
                # Check for both alias keys (from/to) and field name keys (from_date/to_date)
                has_from = (
                    "from" in updated_at_filter or "from_date" in updated_at_filter
                )
                has_to = "to" in updated_at_filter or "to_date" in updated_at_filter
                if has_from and has_to:
                    # It's a DateRangeFilter, extract dates (support both alias and field names)
                    from_date = updated_at_filter.get("from") or updated_at_filter.get(
                        "from_date"
                    )
                    to_date = updated_at_filter.get("to") or updated_at_filter.get(
                        "to_date"
                    )

                    # Remove the original updated_at filter and we'll handle it separately
                    del processed_filters["updated_at"]

                    # Store the date range info for later processing
                    processed_filters["_date_range_updated_at"] = {
                        "from": from_date,
                        "to": to_date,
                    }
            # Also check if it's a Pydantic BaseModel instance (DateRangeFilter)
            elif hasattr(updated_at_filter, "from_date") and hasattr(
                updated_at_filter, "to_date"
            ):
                # It's a DateRangeFilter Pydantic model instance
                from_date = updated_at_filter.from_date
                to_date = updated_at_filter.to_date

                # Remove the original updated_at filter and we'll handle it separately
                del processed_filters["updated_at"]

                # Store the date range info for later processing
                processed_filters["_date_range_updated_at"] = {
                    "from": from_date,
                    "to": to_date,
                }

        # Check if tags is a list (direct array filter)
        if "tags" in processed_filters:
            tags_filter = processed_filters.get("tags")
            # If it's a direct list (not a SearchOperator), handle it separately
            if isinstance(tags_filter, list):
                # Remove from processed_filters and handle separately using array overlap
                del processed_filters["tags"]
                processed_filters["_tags_filter"] = tags_filter

        return processed_filters

    def search(self, filters: Dict[str, Any]) -> List[Entry]:
        query = self.db.query(Entry).options(
            joinedload(Entry.source),
            joinedload(Entry.source_author).joinedload(SourceAuthor.author),
            selectinload(Entry.entry_updates),
        )
        processed_filters = self._process_date_range_filters(filters)
        query = apply_filters(query, Entry, processed_filters)

        # Apply date range filters if present
        if "_date_range_created_at" in processed_filters:
            date_range = processed_filters["_date_range_created_at"]
            from_date = date_range["from"]
            to_date = date_range["to"]

            # Ensure dates are datetime objects (handle case where they might be strings)
            if isinstance(from_date, str):
                from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            if isinstance(to_date, str):
                to_date = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

            query = query.filter(
                Entry.created_at >= from_date, Entry.created_at <= to_date
            )

        if "_date_range_updated_at" in processed_filters:
            date_range = processed_filters["_date_range_updated_at"]
            from_date = date_range["from"]
            to_date = date_range["to"]

            # Ensure dates are datetime objects (handle case where they might be strings)
            if isinstance(from_date, str):
                from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            if isinstance(to_date, str):
                to_date = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

            query = query.filter(
                Entry.updated_at >= from_date, Entry.updated_at <= to_date
            )

        # Apply tags filter if present (using PostgreSQL array overlap for "ANY of these tags")
        if "_tags_filter" in processed_filters:
            tags = processed_filters["_tags_filter"]
            query = query.filter(Entry.tags.overlap(tags))

        return query.all()

    def search_query(self, filters: Dict[str, Any]):
        """Get a query object for entry search for use with fastapi-pagination."""
        query = self.db.query(Entry).options(
            joinedload(Entry.source),
            joinedload(Entry.source_author).joinedload(SourceAuthor.author),
            selectinload(Entry.entry_updates),
        )
        processed_filters = self._process_date_range_filters(filters)
        query = apply_filters(query, Entry, processed_filters)

        # Apply date range filters if present
        if "_date_range_created_at" in processed_filters:
            date_range = processed_filters["_date_range_created_at"]
            from_date = date_range["from"]
            to_date = date_range["to"]

            # Ensure dates are datetime objects (handle case where they might be strings)
            if isinstance(from_date, str):
                from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            if isinstance(to_date, str):
                to_date = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

            query = query.filter(
                Entry.created_at >= from_date, Entry.created_at <= to_date
            )

        if "_date_range_updated_at" in processed_filters:
            date_range = processed_filters["_date_range_updated_at"]
            from_date = date_range["from"]
            to_date = date_range["to"]

            # Ensure dates are datetime objects (handle case where they might be strings)
            if isinstance(from_date, str):
                from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            if isinstance(to_date, str):
                to_date = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

            query = query.filter(
                Entry.updated_at >= from_date, Entry.updated_at <= to_date
            )

        # Apply tags filter if present (using PostgreSQL array overlap for "ANY of these tags")
        if "_tags_filter" in processed_filters:
            tags = processed_filters["_tags_filter"]
            query = query.filter(Entry.tags.overlap(tags))

        return query
