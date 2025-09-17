import pytest
from app.models.gazette import Gazette
from sqlalchemy.orm import Session


@pytest.fixture
def setup_gazette(db: Session, setup_project, faker):
    """Create a test gazette in the database."""
    project = setup_project

    gazette_data = {
        "header": faker.sentence(nb_words=4),
        "subheader": faker.sentence(nb_words=6),
        "theme": faker.word(),
        "tags": [faker.word() for _ in range(3)],
        "labels": {"category": faker.word(), "priority": faker.random_int(1, 5)},
        "project_id": project.id,
        "share_key": faker.uuid4(),
    }

    gazette = Gazette(**gazette_data)
    db.add(gazette)
    db.commit()
    db.refresh(gazette)
    return gazette


@pytest.fixture
def setup_gazette_minimal(db: Session, setup_project, faker):
    """Create a minimal test gazette with only required fields."""
    project = setup_project

    gazette_data = {
        "header": faker.sentence(nb_words=3),
        "project_id": project.id,
    }

    gazette = Gazette(**gazette_data)
    db.add(gazette)
    db.commit()
    db.refresh(gazette)
    return gazette


@pytest.fixture
def setup_gazette_with_share_key(db: Session, setup_project, faker):
    """Create a test gazette with a specific share key."""
    project = setup_project

    gazette_data = {
        "header": faker.sentence(nb_words=4),
        "subheader": faker.sentence(nb_words=6),
        "theme": faker.word(),
        "tags": [faker.word() for _ in range(2)],
        "labels": {"status": "published"},
        "project_id": project.id,
        "share_key": "test-share-key-123",
    }

    gazette = Gazette(**gazette_data)
    db.add(gazette)
    db.commit()
    db.refresh(gazette)
    return gazette
