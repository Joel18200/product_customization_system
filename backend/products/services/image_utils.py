"""
Image utility functions for the Product Customization System.

Provides common image operations: validation, resizing, thumbnails,
color space conversions, and cache key generation.
"""
import os
import hashlib
import logging
from typing import Tuple, Optional, List

import cv2
import numpy as np
from PIL import Image

from django.conf import settings

logger = logging.getLogger(__name__)

# Allowed MIME types
ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"]


def validate_image(file) -> dict:
    """
    Validate an uploaded image file.

    Returns:
        Dict with: valid (bool), error (str|None), width, height,
        file_size, mime_type
    """
    result = {
        "valid": False,
        "error": None,
        "width": None,
        "height": None,
        "file_size": 0,
        "mime_type": "",
    }

    try:
        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        result["file_size"] = file_size

        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 20 * 1024 * 1024)
        if file_size > max_size:
            result["error"] = (
                f"File too large: {file_size / 1024 / 1024:.1f}MB "
                f"(max {max_size / 1024 / 1024:.0f}MB)"
            )
            return result

        # Check image can be opened
        img = Image.open(file)
        img.verify()
        file.seek(0)

        # Re-open after verify
        img = Image.open(file)
        result["width"] = img.width
        result["height"] = img.height

        # Check MIME type
        mime_map = {
            "PNG": "image/png",
            "JPEG": "image/jpeg",
            "WEBP": "image/webp",
        }
        mime = mime_map.get(img.format, f"image/{img.format.lower()}" if img.format else "unknown")
        result["mime_type"] = mime

        allowed = getattr(settings, "ALLOWED_IMAGE_TYPES", ALLOWED_TYPES)
        if mime not in allowed:
            result["error"] = f"Unsupported image type: {mime}"
            return result

        # Check minimum dimensions
        if img.width < 50 or img.height < 50:
            result["error"] = "Image too small (minimum 50x50 pixels)"
            return result

        # Check maximum dimensions
        if img.width > 10000 or img.height > 10000:
            result["error"] = "Image too large (maximum 10000x10000 pixels)"
            return result

        file.seek(0)
        result["valid"] = True
        return result

    except Exception as e:
        result["error"] = f"Invalid image file: {str(e)}"
        return result


def generate_thumbnail(
    image_path: str,
    max_size: int = 300,
    suffix: str = "_thumb",
) -> Optional[str]:
    """
    Generate a thumbnail for an image file.

    Args:
        image_path: Path to the source image
        max_size: Maximum dimension (width or height)
        suffix: Suffix to add before file extension

    Returns:
        Path to the generated thumbnail, or None on failure.
    """
    try:
        img = Image.open(image_path)
        img.thumbnail((max_size, max_size), Image.LANCZOS)

        # Build thumbnail path
        base, ext = os.path.splitext(image_path)
        thumb_path = f"{base}{suffix}{ext}"

        img.save(thumb_path, quality=85, optimize=True)
        logger.debug(f"Thumbnail generated: {thumb_path}")
        return thumb_path

    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return None


def resize_preserve_aspect(
    image: np.ndarray,
    max_dimension: int,
) -> np.ndarray:
    """Resize image so largest dimension equals max_dimension."""
    h, w = image.shape[:2]
    if max(h, w) <= max_dimension:
        return image

    if w >= h:
        new_w = max_dimension
        new_h = int(h * max_dimension / w)
    else:
        new_h = max_dimension
        new_w = int(w * max_dimension / h)

    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_cache_key(
    product_view_id: int,
    design_id: int,
    design_settings: dict,
    quality: str,
) -> str:
    """
    Generate a cache key for a rendered image based on all parameters
    that affect the output.
    """
    key_data = f"{product_view_id}:{design_id}:{quality}:"
    # Sort settings for consistent hashing
    if design_settings:
        sorted_settings = sorted(design_settings.items())
        key_data += str(sorted_settings)
    return hashlib.md5(key_data.encode()).hexdigest()


def has_transparency(image_path: str) -> bool:
    """Check if an image has transparency."""
    try:
        img = Image.open(image_path)
        return img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        )
    except Exception:
        return False


def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
    """Get image width and height."""
    try:
        img = Image.open(image_path)
        return img.width, img.height
    except Exception:
        return None
