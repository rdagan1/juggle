from celery import Celery
from app.config import settings

celery_app = Celery(
    "juggle",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jerusalem",
    enable_utc=True,
)
