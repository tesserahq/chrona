# pyright: reportMissingTypeStubs=false
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery("worker")

celery_app.conf.update(
    broker_url=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    result_backend=f"redis://{settings.redis_host}:{settings.redis_port}/0",
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])  # ensure tasks are registered explicitly
