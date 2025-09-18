import pytest
from app.models.section import Section
from sqlalchemy.orm import Session


@pytest.fixture
def setup_section(db: Session, setup_gazette, faker):
    """Create a test section in the database."""
    gazette = setup_gazette

    section_data = {
        "name": faker.word(),
        "header": faker.sentence(nb_words=4),
        "subheader": faker.sentence(nb_words=6),
        "tags": [faker.word() for _ in range(3)],
        "labels": {"category": faker.word(), "priority": faker.random_int(1, 5)},
        "gazette_id": gazette.id,
    }

    section = Section(**section_data)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@pytest.fixture
def setup_section_minimal(db: Session, setup_gazette, faker):
    """Create a minimal test section with only required fields."""
    gazette = setup_gazette

    section_data = {
        "name": faker.word(),
        "header": faker.sentence(nb_words=3),
        "gazette_id": gazette.id,
    }

    section = Section(**section_data)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@pytest.fixture
def setup_another_section(db: Session, setup_gazette, faker):
    """Create another test section for comparison tests."""
    gazette = setup_gazette

    section_data = {
        "name": faker.word(),
        "header": faker.sentence(nb_words=5),
        "subheader": faker.sentence(nb_words=4),
        "tags": [faker.word() for _ in range(2)],
        "labels": {"status": "published", "importance": faker.word()},
        "gazette_id": gazette.id,
    }

    section = Section(**section_data)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section
