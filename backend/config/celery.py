"""
Celery configuration for the Product Customization System.

Sets up the Celery application with Django settings integration,
automatic task discovery, and periodic cleanup schedules.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("customization_system")

# Load config from Django settings, using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Periodic task schedule (Celery Beat)
app.conf.beat_schedule = {
    "cleanup-expired-previews": {
        "task": "products.tasks.cleanup_expired_previews",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "cleanup-orphaned-uploads": {
        "task": "products.tasks.cleanup_orphaned_uploads",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}

# Task configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,       # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=100,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
