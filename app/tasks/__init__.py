# Import celery app first
from app.core.celery_app import celery_app


# Import tasks for autodiscovery (using lazy imports to avoid heavy dependencies)
def _import_tasks():
    """Import tasks for registration."""
    try:
        from . import process_import_items  # noqa: F401
        from . import backfill_digests  # noqa: F401
    except ImportError:
        pass


_import_tasks()

__all__ = ["celery_app"]
