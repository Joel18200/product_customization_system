"""
Redis-based caching service for rendered images.

Caches render results to avoid re-processing identical configurations.
Falls back gracefully when Redis is unavailable.
"""
import logging
from django.core.cache import cache
from products.services.image_utils import compute_cache_key

logger = logging.getLogger(__name__)

# Cache TTLs in seconds
PREVIEW_CACHE_TTL = 3600       # 1 hour for previews
FINAL_RENDER_CACHE_TTL = 86400  # 24 hours for final renders


def get_cached_render(
    product_view_id: int,
    design_id: int,
    design_settings: dict,
    quality: str,
) -> str | None:
    """
    Check if a render result exists in cache.

    Returns:
        Cached output image path (relative to MEDIA_ROOT) or None.
    """
    key = _make_key(product_view_id, design_id, design_settings, quality)
    try:
        return cache.get(key)
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
        return None


def set_cached_render(
    product_view_id: int,
    design_id: int,
    design_settings: dict,
    quality: str,
    output_path: str,
) -> None:
    """
    Store a render result in cache.

    Args:
        output_path: The relative media path to the rendered image.
    """
    key = _make_key(product_view_id, design_id, design_settings, quality)
    ttl = FINAL_RENDER_CACHE_TTL if quality == "final" else PREVIEW_CACHE_TTL
    try:
        cache.set(key, output_path, ttl)
        logger.debug(f"Cached render: key={key}, ttl={ttl}s")
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")


def invalidate_render_cache(
    product_view_id: int = None,
    design_id: int = None,
) -> None:
    """
    Invalidate cached renders when source images change.
    Since we can't do pattern-based invalidation with all backends,
    we rely on TTL expiry for most cases.
    """
    # With Redis, we could do pattern-based deletion.
    # For now, log the invalidation request.
    logger.info(
        f"Cache invalidation requested: "
        f"product_view={product_view_id}, design={design_id}"
    )


def _make_key(
    product_view_id: int,
    design_id: int,
    design_settings: dict,
    quality: str,
) -> str:
    """Generate a prefixed cache key."""
    raw = compute_cache_key(product_view_id, design_id, design_settings, quality)
    return f"render:{raw}"
