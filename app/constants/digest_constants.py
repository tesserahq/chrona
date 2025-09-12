class DigestStatuses:
    """Digest status constants."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    @classmethod
    def get_all(cls):
        return [cls.DRAFT, cls.PUBLISHED, cls.ARCHIVED]
