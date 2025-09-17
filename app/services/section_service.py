from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.section import Section
from app.schemas.section import SectionCreate, SectionUpdate
from app.services.soft_delete_service import SoftDeleteService
from app.utils.db.filtering import apply_filters


class SectionService(SoftDeleteService[Section]):
    """Service class for managing Section entities."""

    def __init__(self, db: Session):
        super().__init__(db, Section)

    def get_section(self, section_id: UUID) -> Optional[Section]:
        """Get a single section by ID."""
        return self.db.query(Section).filter(Section.id == section_id).first()

    def get_sections(self, skip: int = 0, limit: int = 100) -> List[Section]:
        """Get a list of sections with pagination."""
        return self.db.query(Section).offset(skip).limit(limit).all()

    def get_sections_by_gazette(
        self, gazette_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Section]:
        """Get sections belonging to a specific gazette."""
        return (
            self.db.query(Section)
            .filter(Section.gazette_id == gazette_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_section(self, section: SectionCreate) -> Section:
        """Create a new section."""
        section_data = section.model_dump()
        db_section = Section(**section_data)
        self.db.add(db_section)
        self.db.commit()
        self.db.refresh(db_section)
        return db_section

    def update_section(
        self, section_id: UUID, section: SectionUpdate
    ) -> Optional[Section]:
        """Update a section."""
        db_section = self.db.query(Section).filter(Section.id == section_id).first()
        if db_section:
            update_data = section.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_section, key, value)
            self.db.commit()
            self.db.refresh(db_section)
        return db_section

    def delete_section(self, section_id: UUID) -> bool:
        """Soft delete a section."""
        return self.delete_record(section_id)

    def search(self, filters: Dict[str, Any]) -> List[Section]:
        """Search sections with filters."""
        query = self.db.query(Section)
        query = apply_filters(query, Section, filters)
        return query.all()
