from uuid import uuid4
from app.services.section_service import SectionService
from app.schemas.section import SectionCreate, SectionUpdate
from app.models.section import Section


class TestSectionService:
    """Test suite for SectionService."""

    def test_get_section_success(self, db, setup_section):
        """Test getting a section by ID successfully."""
        section = setup_section
        service = SectionService(db)

        result = service.get_section(section.id)

        assert result is not None
        assert result.id == section.id
        assert result.header == section.header
        assert result.gazette_id == section.gazette_id

    def test_get_section_not_found(self, db):
        """Test getting a non-existent section returns None."""
        service = SectionService(db)
        non_existent_id = uuid4()

        result = service.get_section(non_existent_id)

        assert result is None

    def test_get_sections_with_pagination(
        self, db, setup_section, setup_another_section
    ):
        """Test getting sections with pagination."""
        section1 = setup_section
        section2 = setup_another_section
        service = SectionService(db)

        # Test default pagination
        result = service.get_sections()
        assert len(result) >= 2

        # Test with limit
        result = service.get_sections(limit=1)
        assert len(result) == 1

        # Test with skip
        result = service.get_sections(skip=1, limit=1)
        assert len(result) == 1

    def test_get_sections_by_gazette(
        self, db, setup_section, setup_another_section, setup_gazette, faker
    ):
        """Test getting sections by gazette ID."""
        gazette = setup_gazette
        section1 = setup_section  # Uses setup_gazette

        # Create another gazette and section for testing filtering
        from app.models.gazette import Gazette

        other_gazette_data = {
            "header": faker.sentence(nb_words=4),
            "project_id": gazette.project_id,
        }
        other_gazette = Gazette(**other_gazette_data)
        db.add(other_gazette)
        db.commit()
        db.refresh(other_gazette)


        other_section_data = {
            "header": faker.sentence(nb_words=3),
            "gazette_id": other_gazette.id,
        }
        other_section = Section(**other_section_data)
        db.add(other_section)
        db.commit()
        db.refresh(other_section)

        service = SectionService(db)

        # Get sections for first gazette
        result = service.get_sections_by_gazette(gazette.id)
        section_ids = [s.id for s in result]
        assert section1.id in section_ids
        assert other_section.id not in section_ids

        # Get sections for second gazette
        result = service.get_sections_by_gazette(other_gazette.id)
        section_ids = [s.id for s in result]
        assert other_section.id in section_ids
        assert section1.id not in section_ids

    def test_create_section_success(self, db, setup_gazette, faker):
        """Test creating a section successfully."""
        gazette = setup_gazette
        service = SectionService(db)

        section_data = SectionCreate(
            header=faker.sentence(nb_words=4),
            subheader=faker.sentence(nb_words=6),
            tags=[faker.word() for _ in range(3)],
            labels={"category": faker.word()},
            gazette_id=gazette.id,
        )

        result = service.create_section(section_data)

        assert result is not None
        assert result.id is not None
        assert result.header == section_data.header
        assert result.subheader == section_data.subheader
        assert result.tags == section_data.tags
        assert result.labels == section_data.labels
        assert result.gazette_id == section_data.gazette_id
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_section_minimal(self, db, setup_gazette, faker):
        """Test creating a section with minimal required fields."""
        gazette = setup_gazette
        service = SectionService(db)

        section_data = SectionCreate(
            header=faker.sentence(nb_words=3),
            gazette_id=gazette.id,
        )

        result = service.create_section(section_data)

        assert result is not None
        assert result.id is not None
        assert result.header == section_data.header
        assert result.subheader is None
        assert result.tags == []
        assert result.labels == {}
        assert result.gazette_id == section_data.gazette_id

    def test_update_section_success(self, db, setup_section, faker):
        """Test updating a section successfully."""
        section = setup_section
        service = SectionService(db)

        new_header = faker.sentence(nb_words=5)
        new_subheader = faker.sentence(nb_words=7)
        new_tags = [faker.word() for _ in range(2)]
        new_labels = {"updated": True, "priority": faker.random_int(1, 10)}

        update_data = SectionUpdate(
            header=new_header,
            subheader=new_subheader,
            tags=new_tags,
            labels=new_labels,
        )

        result = service.update_section(section.id, update_data)

        assert result is not None
        assert result.id == section.id
        assert result.header == new_header
        assert result.subheader == new_subheader
        assert result.tags == new_tags
        assert result.labels == new_labels
        assert result.gazette_id == section.gazette_id  # Should remain unchanged

    def test_update_section_partial(self, db, setup_section, faker):
        """Test partially updating a section."""
        section = setup_section
        service = SectionService(db)
        original_subheader = section.subheader
        original_tags = section.tags
        original_labels = section.labels

        new_header = faker.sentence(nb_words=4)
        update_data = SectionUpdate(header=new_header)

        result = service.update_section(section.id, update_data)

        assert result is not None
        assert result.header == new_header
        assert result.subheader == original_subheader
        assert result.tags == original_tags
        assert result.labels == original_labels

    def test_update_section_not_found(self, db, faker):
        """Test updating a non-existent section returns None."""
        service = SectionService(db)
        non_existent_id = uuid4()

        update_data = SectionUpdate(header=faker.sentence(nb_words=3))
        result = service.update_section(non_existent_id, update_data)

        assert result is None

    def test_delete_section_success(self, db, setup_section):
        """Test soft deleting a section successfully."""
        section = setup_section
        service = SectionService(db)

        result = service.delete_section(section.id)

        assert result is True

        # Verify the section is soft deleted
        db.refresh(section)
        assert section.deleted_at is not None

    def test_delete_section_not_found(self, db):
        """Test deleting a non-existent section returns False."""
        service = SectionService(db)
        non_existent_id = uuid4()

        result = service.delete_section(non_existent_id)

        assert result is False

    def test_search_sections_with_filters(
        self, db, setup_section, setup_another_section
    ):
        """Test searching sections with filters."""
        section1 = setup_section
        section2 = setup_another_section
        service = SectionService(db)

        # Test filtering by gazette_id
        filters = {"gazette_id": section1.gazette_id}
        result = service.search(filters)

        section_ids = [s.id for s in result]
        assert section1.id in section_ids
        # Both sections should have the same gazette_id from fixtures
        assert section2.id in section_ids

    def test_search_sections_no_filters(self, db, setup_section, setup_another_section):
        """Test searching sections without filters returns all."""
        section1 = setup_section
        section2 = setup_another_section
        service = SectionService(db)

        result = service.search({})

        assert len(result) >= 2
        section_ids = [s.id for s in result]
        assert section1.id in section_ids
        assert section2.id in section_ids
