"""
Celery tasks for the Product Customization System.

Handles async rendering (preview, final, thumbnail), batch processing,
and periodic cleanup operations.
"""
import os
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="products.tasks.generate_preview_task",
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=30,
    time_limit=60,
)
def generate_preview_task(self, job_id: int):
    """
    Async preview generation. Should complete in <2 seconds.
    """
    try:
        from products.services.renderer import generate_preview
        from products.services.cache_service import get_cached_render, set_cached_render
        from products.models import CustomizationJob

        job = CustomizationJob.objects.select_related(
            "design", "product_view"
        ).get(id=job_id)

        # Check cache first
        cached = get_cached_render(
            job.product_view_id, job.design_id,
            job.design_settings or {}, "preview"
        )
        if cached:
            job.output_image = cached
            job.status = "completed"
            job.save(update_fields=["output_image", "status"])
            logger.info(f"Preview served from cache: job={job_id}")
            return {"job_id": job_id, "status": "completed", "cached": True}

        # Generate preview
        result = generate_preview(job_id)

        # Cache the result
        if result.output_image:
            set_cached_render(
                job.product_view_id, job.design_id,
                job.design_settings or {}, "preview",
                str(result.output_image)
            )

        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:
        logger.error(f"Preview task failed for job {job_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="products.tasks.generate_final_render_task",
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def generate_final_render_task(self, render_job_id: int):
    """
    Async final render generation. Should complete in <5 seconds.
    """
    try:
        from products.services.renderer import run_render_job

        result = run_render_job(render_job_id)
        return {
            "render_job_id": render_job_id,
            "status": result.status,
            "output": str(result.output_image) if result.output_image else None,
        }

    except Exception as exc:
        logger.error(f"Final render failed: render_job={render_job_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="products.tasks.generate_thumbnail_task",
    soft_time_limit=15,
    time_limit=30,
)
def generate_thumbnail_task(image_path: str, max_size: int = 300):
    """Generate a thumbnail for any image."""
    try:
        from products.services.image_utils import generate_thumbnail

        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        thumb_path = generate_thumbnail(full_path, max_size=max_size)
        return {"source": image_path, "thumbnail": thumb_path}

    except Exception as exc:
        logger.error(f"Thumbnail generation failed for {image_path}: {exc}")
        return {"source": image_path, "error": str(exc)}


@shared_task(
    bind=True,
    name="products.tasks.batch_render_task",
    soft_time_limit=600,
    time_limit=900,
)
def batch_render_task(self, job_ids: list):
    """Process multiple render jobs sequentially."""
    results = []
    for i, job_id in enumerate(job_ids):
        try:
            from products.services.renderer import generate_preview

            self.update_state(
                state="PROGRESS",
                meta={"current": i + 1, "total": len(job_ids)}
            )
            generate_preview(job_id)
            results.append({"job_id": job_id, "status": "completed"})
        except Exception as e:
            results.append({"job_id": job_id, "status": "failed", "error": str(e)})
            logger.error(f"Batch render failed for job {job_id}: {e}")

    return {"total": len(job_ids), "results": results}


@shared_task(name="products.tasks.cleanup_expired_previews")
def cleanup_expired_previews():
    """
    Periodic task: Remove preview images older than 7 days.
    Runs daily at 2 AM (configured in celery.py beat schedule).
    """
    preview_dir = os.path.join(settings.MEDIA_ROOT, "generated_previews")
    if not os.path.exists(preview_dir):
        return {"deleted": 0}

    cutoff = timezone.now() - timedelta(days=7)
    deleted = 0

    for filename in os.listdir(preview_dir):
        filepath = os.path.join(preview_dir, filename)
        if os.path.isfile(filepath):
            mtime = os.path.getmtime(filepath)
            file_time = timezone.datetime.fromtimestamp(
                mtime, tz=timezone.utc
            )
            if file_time < cutoff:
                os.remove(filepath)
                deleted += 1

    logger.info(f"Cleaned up {deleted} expired preview files")
    return {"deleted": deleted}


@shared_task(name="products.tasks.cleanup_orphaned_uploads")
def cleanup_orphaned_uploads():
    """
    Periodic task: Remove uploaded designs with no associated customization
    jobs that are older than 24 hours.
    """
    from products.models import DesignUpload

    cutoff = timezone.now() - timedelta(hours=24)
    orphans = DesignUpload.objects.filter(
        customizations__isnull=True,
        uploaded_at__lt=cutoff,
    )

    count = orphans.count()
    for upload in orphans:
        # Delete the file
        if upload.image and os.path.exists(upload.image.path):
            os.remove(upload.image.path)
        if upload.thumbnail and os.path.exists(upload.thumbnail.path):
            os.remove(upload.thumbnail.path)
        upload.delete()

    logger.info(f"Cleaned up {count} orphaned uploads")
    return {"deleted": count}
