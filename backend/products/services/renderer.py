"""
Render service orchestrator.

Bridges the Django models with the OpenCV rendering pipeline.
Handles image loading, saving, and model status updates.
"""
import time
import logging
import cv2
import numpy as np
from django.core.files.base import ContentFile

from products.models import CustomizationJob, PrintArea, RenderJob
from products.services.opencv_renderer import render_design_on_arrays

logger = logging.getLogger(__name__)


def _imread_field(field, flags):
    """
    Decode an ImageField's file into an OpenCV image array, reading through the
    field's storage backend so it works with both the local filesystem and
    remote storage (e.g. Cloudinary). Avoids relying on ``.path``, which remote
    backends don't support.
    """
    with field.open("rb") as fh:
        data = fh.read()
    buf = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(buf, flags)


def _encode_png(image, high_quality=False):
    """Encode a BGR(A) array to PNG bytes."""
    params = [cv2.IMWRITE_PNG_COMPRESSION, 1] if high_quality else []
    ok, buf = cv2.imencode(".png", image, params)
    if not ok:
        raise ValueError("Failed to encode rendered image to PNG")
    return buf.tobytes()


def _surface_for(product_view) -> str:
    """
    Decide which surface model the pipeline should use for a view.
    Caps/visors/beanies are curved crowns → cylindrical curvature; everything
    else (tees, hoodies front/back) is treated as flat.
    """
    name = f"{product_view.product.name} {product_view.view_name}".lower()
    if any(w in name for w in ("cap", "visor", "beanie", "hat")):
        return "cap"
    return "flat"


def generate_preview(job_id: int) -> CustomizationJob:
    """
    Generate a preview render for a customization job.
    This is the original entry point — preserved for backward compatibility.
    Now delegates to the advanced OpenCV pipeline.
    """
    return _run_render(job_id, quality="preview")


def generate_final_render(job_id: int) -> CustomizationJob:
    """Generate a full-quality render for a customization job."""
    return _run_render(job_id, quality="final")


def _run_render(job_id: int, quality: str = "preview") -> CustomizationJob:
    """
    Core render execution: loads models, runs the pipeline, saves output.
    """
    job = CustomizationJob.objects.select_related(
        "design", "product_view"
    ).get(id=job_id)

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        design = job.design
        product_view = job.product_view

        # Get print area for this view
        print_area = PrintArea.objects.filter(
            product_view=product_view
        ).first()

        if not print_area:
            raise ValueError(
                f"No print area configured for product view: {product_view}"
            )

        # Build print area dict
        pa_dict = {
            "x": print_area.x,
            "y": print_area.y,
            "width": print_area.width,
            "height": print_area.height,
            "rotation": print_area.rotation,
        }

        # Get user design settings
        design_settings = job.design_settings or {}

        # Load source images through their storage backend (local or remote)
        product_img = _imread_field(product_view.image, cv2.IMREAD_COLOR)
        design_img = _imread_field(design.image, cv2.IMREAD_UNCHANGED)

        # Run the rendering pipeline
        start_time = time.time()
        result_image, timings = render_design_on_arrays(
            product=product_img,
            design=design_img,
            print_area=pa_dict,
            design_settings=design_settings,
            quality=quality,
            surface=_surface_for(product_view),
        )
        total_time = time.time() - start_time

        # Save output image through storage (uploads to Cloudinary in prod).
        # The field's upload_to ("generated_previews/") supplies the folder.
        prefix = "preview" if quality == "preview" else "final"
        output_filename = f"{prefix}_{job.id}_{int(time.time())}.png"
        png_bytes = _encode_png(result_image, high_quality=(quality == "final"))

        job.output_image.save(output_filename, ContentFile(png_bytes), save=False)
        job.status = "completed"
        job.save(update_fields=["output_image", "status"])

        logger.info(
            f"Render complete: job={job_id}, quality={quality}, "
            f"time={total_time:.2f}s, timings={timings}"
        )

        return job

    except Exception as e:
        logger.error(f"Render failed for job {job_id}: {e}", exc_info=True)
        job.status = "failed"
        job.save(update_fields=["status"])
        raise


def run_render_job(render_job_id: int) -> RenderJob:
    """
    Execute a render job (used by Celery tasks).
    Updates the RenderJob model with progress and results.
    """
    from django.utils import timezone

    render_job = RenderJob.objects.select_related(
        "customization", "customization__design",
        "customization__product_view"
    ).get(id=render_job_id)

    try:
        render_job.status = "processing"
        render_job.started_at = timezone.now()
        render_job.progress = 10
        render_job.save(update_fields=["status", "started_at", "progress"])

        quality = "final" if render_job.render_type == "final" else "preview"
        job = render_job.customization

        design = job.design
        product_view = job.product_view

        print_area = PrintArea.objects.filter(
            product_view=product_view
        ).first()

        if not print_area:
            raise ValueError("No print area configured")

        pa_dict = {
            "x": print_area.x,
            "y": print_area.y,
            "width": print_area.width,
            "height": print_area.height,
            "rotation": print_area.rotation,
        }

        render_job.progress = 30
        render_job.save(update_fields=["progress"])

        # Load source images through storage (local or remote)
        product_img = _imread_field(product_view.image, cv2.IMREAD_COLOR)
        design_img = _imread_field(design.image, cv2.IMREAD_UNCHANGED)

        # Run pipeline
        result_image, timings = render_design_on_arrays(
            product=product_img,
            design=design_img,
            print_area=pa_dict,
            design_settings=job.design_settings or {},
            quality=quality,
            surface=_surface_for(product_view),
        )

        render_job.progress = 80
        render_job.save(update_fields=["progress"])

        # Save output through storage (uploads to Cloudinary in prod).
        output_filename = f"render_{render_job.id}_{int(time.time())}.png"
        png_bytes = _encode_png(result_image, high_quality=(quality == "final"))
        render_job.output_image.save(
            output_filename, ContentFile(png_bytes), save=False
        )

        # Update render job
        render_job.status = "completed"
        render_job.progress = 100
        render_job.completed_at = timezone.now()
        render_job.render_metadata = {
            "timings": timings,
            "output_size": len(png_bytes),
            "dimensions": [result_image.shape[1], result_image.shape[0]],
        }
        render_job.save()

        # Also update the parent customization job
        job.output_image = render_job.output_image
        job.status = "completed"
        job.save(update_fields=["output_image", "status"])

        return render_job

    except Exception as e:
        logger.error(
            f"RenderJob {render_job_id} failed: {e}", exc_info=True
        )
        render_job.status = "failed"
        render_job.error_message = str(e)
        render_job.completed_at = timezone.now()
        render_job.save(update_fields=[
            "status", "error_message", "completed_at"
        ])
        raise
