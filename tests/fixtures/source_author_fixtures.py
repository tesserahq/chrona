import pytest
from app.models.source_author import SourceAuthor


@pytest.fixture
def setup_source_author(db, faker, setup_source, setup_author):
    """Create a test source author in the database."""
    source = setup_source
    author = setup_author

    source_author_data = {
        "author_id": author.id,
        "source_id": source.id,
        "source_author_id": str(faker.uuid4()),
    }
    source_author = SourceAuthor(**source_author_data)
    db.add(source_author)
    db.commit()
    db.refresh(source_author)
    return source_author
