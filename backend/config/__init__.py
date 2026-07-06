"""
Config package initialization.
Ensures the Celery app is loaded when Django starts.
"""
try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except ImportError:
    # Celery not installed — graceful degradation for dev/testing
    celery_app = None
    __all__ = ()
