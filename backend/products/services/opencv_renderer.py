"""
Advanced Rendering Pipeline using OpenCV, NumPy, and Pillow.

Implements the 5-stage rendering process:
  1. Validation & Preparation
  2. Print Area Placement
  3. Perspective Detection & Transform
  4. Fabric Conformation (Displacement Mapping)
  5. Realistic Blending

The result looks like the design is actually printed on the fabric,
not pasted on top.
"""
import cv2
import numpy as np
import logging
import time
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class RenderPipeline:
    """
    Core rendering engine that transforms a flat design image into a
    realistic product mockup by applying perspective transforms,
    fabric displacement, and photorealistic blending.
    """

    def __init__(self, quality: str = "preview", surface: str = "flat"):
        """
        Args:
            quality: "preview" for fast rendering, "final" for high quality.
            surface: "flat" (tees/hoodies front/back) or "cap" (curved crown) —
                     controls whether a cylindrical curvature warp is applied.
        """
        self.quality = quality
        self.surface = surface
        # Scale factor for internal processing
        self.scale = 0.5 if quality == "preview" else 1.0
        self.timings: Dict[str, float] = {}

    def render(
        self,
        product_image: np.ndarray,
        design_image: np.ndarray,
        print_area: Dict[str, int],
        design_settings: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        """
        Execute the full rendering pipeline.

        Args:
            product_image: Product photo as BGR numpy array (from cv2.imread)
            design_image: Design artwork as BGRA numpy array (with alpha)
            print_area: Dict with keys x, y, width, height, rotation (optional)
            design_settings: Optional user adjustments (scale, rotation, offsetX, offsetY)

        Returns:
            Rendered product image as BGR numpy array.
        """
        if design_settings is None:
            design_settings = {}

        total_start = time.time()

        # Preview scale is chosen from the SOURCE size: only downscale large
        # product photos (perf); keep small photos (e.g. the 555x405 visor /
        # beanie conf images) at full resolution so the preview isn't shrunk
        # or softened next to the full-res live editor. Large images are
        # unchanged (0.5), so higher-res products don't regress.
        if self.quality == "preview":
            longest = max(product_image.shape[0], product_image.shape[1])
            self.scale = 0.5 if longest > 1400 else 1.0
        else:
            self.scale = 1.0

        # ── Stage 1: Validation & Preparation ──
        t0 = time.time()
        product_img, design_img = self._prepare_images(
            product_image, design_image
        )
        self.timings["preparation"] = time.time() - t0

        # ── Stage 2: Print Area Placement ──
        t0 = time.time()
        placed_design, paste_x, paste_y = self._place_in_print_area(
            design_img, print_area, design_settings
        )
        self.timings["placement"] = time.time() - t0

        # ── Stage 3: Perspective / Curvature ──
        t0 = time.time()
        if self.surface == "cap":
            # Curved crown: the contour-based perspective is noisy on cap
            # panels/seams and skews the design asymmetrically (a round patch
            # comes out squeezed/clipped on one side). Use ONLY the symmetric
            # cylindrical curvature so a circular badge stays a clean circle.
            perspective_design = self._apply_curvature(placed_design)
        else:
            perspective_design = self._apply_perspective(
                placed_design, product_img, print_area, paste_x, paste_y
            )
        self.timings["perspective"] = time.time() - t0

        # ── Stage 4: Fabric Conformation ──
        t0 = time.time()
        conformed_design = self._apply_fabric_conformation(
            perspective_design, product_img, print_area, paste_x, paste_y
        )
        self.timings["conformation"] = time.time() - t0

        # ── Stage 5: Realistic Blending ──
        t0 = time.time()
        result = self._blend_realistic(
            product_img, conformed_design, paste_x, paste_y
        )
        self.timings["blending"] = time.time() - t0

        self.timings["total"] = time.time() - total_start
        logger.info(
            f"Render complete ({self.quality}): "
            f"total={self.timings['total']:.3f}s, "
            f"prep={self.timings['preparation']:.3f}s, "
            f"place={self.timings['placement']:.3f}s, "
            f"persp={self.timings['perspective']:.3f}s, "
            f"conform={self.timings['conformation']:.3f}s, "
            f"blend={self.timings['blending']:.3f}s"
        )

        return result

    # ────────────────────────────────────────────────────────────────
    # Stage 1: Preparation
    # ────────────────────────────────────────────────────────────────

    def _prepare_images(
        self, product: np.ndarray, design: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Validate and prepare images for processing."""
        # Ensure product is BGR
        if len(product.shape) == 2:
            product = cv2.cvtColor(product, cv2.COLOR_GRAY2BGR)
        elif product.shape[2] == 4:
            product = cv2.cvtColor(product, cv2.COLOR_BGRA2BGR)

        # Ensure design has alpha channel
        if len(design.shape) == 2:
            design = cv2.cvtColor(design, cv2.COLOR_GRAY2BGRA)
        elif design.shape[2] == 3:
            # Add full-opacity alpha channel
            alpha = np.full(
                (design.shape[0], design.shape[1], 1), 255, dtype=np.uint8
            )
            design = np.concatenate([design, alpha], axis=2)

        # Scale down for preview quality
        if self.scale < 1.0:
            h, w = product.shape[:2]
            new_w = int(w * self.scale)
            new_h = int(h * self.scale)
            product = cv2.resize(product, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return product, design

    # ────────────────────────────────────────────────────────────────
    # Stage 2: Print Area Placement
    # ────────────────────────────────────────────────────────────────

    def _place_in_print_area(
        self,
        design: np.ndarray,
        print_area: Dict[str, int],
        settings: Dict[str, Any],
    ) -> Tuple[np.ndarray, int, int]:
        """
        Scale, rotate, and position the design within the print area.
        Returns the transformed design and its paste coordinates.
        """
        pa_x = int(print_area["x"] * self.scale)
        pa_y = int(print_area["y"] * self.scale)
        pa_w = int(print_area["width"] * self.scale)
        pa_h = int(print_area["height"] * self.scale)

        # Apply user scale (default: fit 90% of print area)
        user_scale = settings.get("scale", 0.9)
        user_rotation = settings.get("rotation", 0)
        offset_x = int(settings.get("offsetX", 0) * self.scale)
        offset_y = int(settings.get("offsetY", 0) * self.scale)

        # Calculate target dimensions preserving aspect ratio
        target_w = int(pa_w * user_scale)
        dh, dw = design.shape[:2]
        aspect = dw / dh if dh > 0 else 1
        target_h = int(target_w / aspect)

        if target_h > int(pa_h * user_scale):
            target_h = int(pa_h * user_scale)
            target_w = int(target_h * aspect)

        # Resize design
        placed = cv2.resize(
            design, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4
        )

        # Apply rotation if specified
        pa_rotation = print_area.get("rotation", 0)
        total_rotation = user_rotation + pa_rotation
        if abs(total_rotation) > 0.1:
            placed = self._rotate_image(placed, total_rotation)

        # Center in print area + user offset
        center_x = pa_x + pa_w // 2
        center_y = pa_y + pa_h // 2
        paste_x = center_x - placed.shape[1] // 2 + offset_x
        paste_y = center_y - placed.shape[0] // 2 + offset_y

        # Clamp to print area bounds
        paste_x = max(pa_x, min(paste_x, pa_x + pa_w - placed.shape[1]))
        paste_y = max(pa_y, min(paste_y, pa_y + pa_h - placed.shape[0]))

        return placed, paste_x, paste_y

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by angle degrees, expanding canvas to fit."""
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new bounding box
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        M[0, 2] += (new_w - w) / 2
        M[1, 2] += (new_h - h) / 2

        return cv2.warpAffine(
            image, M, (new_w, new_h),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0)
        )

    # ────────────────────────────────────────────────────────────────
    # Stage 3: Perspective Detection & Transform
    # ────────────────────────────────────────────────────────────────

    def _apply_perspective(
        self,
        design: np.ndarray,
        product: np.ndarray,
        print_area: Dict[str, int],
        paste_x: int,
        paste_y: int,
    ) -> np.ndarray:
        """
        Detect the perspective of the product surface and warp the
        design to match.

        Uses edge detection and contour analysis on the print area region
        to find the dominant surface plane, then computes a homography
        to warp the design accordingly.
        """
        pa_x = int(print_area["x"] * self.scale)
        pa_y = int(print_area["y"] * self.scale)
        pa_w = int(print_area["width"] * self.scale)
        pa_h = int(print_area["height"] * self.scale)

        dh, dw = design.shape[:2]

        # Extract ROI around the print area with padding
        pad = int(max(pa_w, pa_h) * 0.15)
        roi_x1 = max(0, pa_x - pad)
        roi_y1 = max(0, pa_y - pad)
        roi_x2 = min(product.shape[1], pa_x + pa_w + pad)
        roi_y2 = min(product.shape[0], pa_y + pa_h + pad)
        roi = product[roi_y1:roi_y2, roi_x1:roi_x2]

        if roi.size == 0:
            return design

        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)

        # Dilate edges to connect nearby contours
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Find contours and look for quadrilateral approximations
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        perspective_quad = None
        if contours:
            # Sort by area, take largest contours
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            for contour in contours[:5]:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    roi_area = roi.shape[0] * roi.shape[1]
                    if area > roi_area * 0.1:
                        perspective_quad = approx.reshape(4, 2).astype(np.float32)
                        break

        if perspective_quad is not None:
            # Order points: top-left, top-right, bottom-right, bottom-left
            perspective_quad = self._order_points(perspective_quad)

            # Source rectangle (flat design corners)
            src_pts = np.float32([
                [0, 0],
                [dw - 1, 0],
                [dw - 1, dh - 1],
                [0, dh - 1],
            ])

            # Map the detected quad to design coordinates
            # Normalize quad relative to the ROI offset
            dst_pts = perspective_quad.copy()
            dst_pts[:, 0] -= (pa_x - roi_x1)
            dst_pts[:, 1] -= (pa_y - roi_y1)

            # Scale to design dimensions
            quad_w = np.max(dst_pts[:, 0]) - np.min(dst_pts[:, 0])
            quad_h = np.max(dst_pts[:, 1]) - np.min(dst_pts[:, 1])
            if quad_w > 0 and quad_h > 0:
                scale_x = dw / quad_w
                scale_y = dh / quad_h
                dst_pts[:, 0] = (dst_pts[:, 0] - np.min(dst_pts[:, 0])) * scale_x
                dst_pts[:, 1] = (dst_pts[:, 1] - np.min(dst_pts[:, 1])) * scale_y

                # Safety clamp: a straight-on garment/cap shot is nearly
                # fronto-parallel. Detected quads can be noisy (seams,
                # pockets, wrinkles), so we constrain each corner's deviation
                # from the ideal rectangle and blend toward identity. This
                # keeps perspective automatic but subtle, preventing
                # unrealistic warping of the design.
                dst_pts = self._constrain_quad(
                    dst_pts, dw, dh, max_dev=0.12, strength=0.5
                )

                # Safety: never let a constrained corner fall outside the
                # design canvas, or warpPerspective would clip it. Corners may
                # still move inward (leaving a transparent margin), which is
                # fine — only outward escape crops the artwork.
                dst_pts[:, 0] = np.clip(dst_pts[:, 0], 0, dw - 1)
                dst_pts[:, 1] = np.clip(dst_pts[:, 1], 0, dh - 1)

                # Compute homography and warp
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if M is not None:
                    warped = cv2.warpPerspective(
                        design, M, (dw, dh),
                        flags=cv2.INTER_LANCZOS4,
                        borderMode=cv2.BORDER_CONSTANT,
                        borderValue=(0, 0, 0, 0)
                    )
                    return warped
        else:
            # Fallback: Apply subtle perspective based on print area position
            # relative to image center (assumes natural camera perspective)
            img_center_x = product.shape[1] / 2
            img_center_y = product.shape[0] / 2
            area_center_x = pa_x + pa_w / 2
            area_center_y = pa_y + pa_h / 2

            # Calculate perspective offset based on position from center
            dx = (area_center_x - img_center_x) / product.shape[1]
            dy = (area_center_y - img_center_y) / product.shape[0]

            # Subtle perspective: shrink edges closer to vanishing point
            shrink = 0.03  # Max perspective distortion
            src_pts = np.float32([
                [0, 0], [dw, 0], [dw, dh], [0, dh]
            ])
            dst_pts = np.float32([
                [dw * shrink * max(0, dx), dh * shrink * max(0, dy)],
                [dw - dw * shrink * max(0, -dx), dh * shrink * max(0, dy)],
                [dw - dw * shrink * max(0, -dx), dh - dh * shrink * max(0, -dy)],
                [dw * shrink * max(0, dx), dh - dh * shrink * max(0, -dy)],
            ])

            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(
                design, M, (dw, dh),
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0)
            )
            return warped

        return design

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order 4 points as: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # Top-left has smallest sum
        rect[2] = pts[np.argmax(s)]  # Bottom-right has largest sum
        d = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(d)]  # Top-right has smallest difference
        rect[3] = pts[np.argmax(d)]  # Bottom-left has largest difference
        return rect

    def _constrain_quad(
        self,
        dst_pts: np.ndarray,
        dw: int,
        dh: int,
        max_dev: float = 0.12,
        strength: float = 0.5,
    ) -> np.ndarray:
        """
        Constrain a detected destination quad toward the canonical rectangle.

        Detected quads on near-frontal product shots are often noisy. To keep
        the automatic perspective realistic, we (1) blend the detected corners
        toward the ideal rectangle by ``strength`` and (2) clamp each corner's
        remaining offset to ``max_dev`` of the design width/height.

        Args:
            dst_pts: 4x2 detected corners (TL, TR, BR, BL) in design space.
            dw, dh: design width/height.
            max_dev: maximum allowed corner offset as a fraction of the size.
            strength: 0 = ignore detection (identity), 1 = full detected quad.

        Returns:
            Constrained 4x2 float32 corners.
        """
        canonical = np.float32([[0, 0], [dw, 0], [dw, dh], [0, dh]])
        # Blend detected quad toward the canonical rectangle.
        blended = canonical + strength * (dst_pts.astype(np.float32) - canonical)
        # Clamp per-corner deviation from the canonical corner.
        max_x = max_dev * dw
        max_y = max_dev * dh
        offset = blended - canonical
        offset[:, 0] = np.clip(offset[:, 0], -max_x, max_x)
        offset[:, 1] = np.clip(offset[:, 1], -max_y, max_y)
        return (canonical + offset).astype(np.float32)


    # ────────────────────────────────────────────────────────────────
    # Stage 4: Fabric Conformation (Displacement Mapping)
    # ────────────────────────────────────────────────────────────────

    def _apply_fabric_conformation(
        self,
        design: np.ndarray,
        product: np.ndarray,
        print_area: Dict[str, int],
        paste_x: int,
        paste_y: int,
    ) -> np.ndarray:
        """
        Warp the design so it conforms to the fabric's folds, wrinkles and seams.

        Root-cause fix vs. the previous version:
          * Displacement magnitude is now **relative to the design size**
            (a fraction of the ROI width) instead of a fixed 3-6px, so it is
            actually visible on high-resolution product photos.
          * The displacement field is derived from a **smoothed luminance
            "height field"** and normalised **locally** (per-pixel, via a
            blurred gradient magnitude) rather than dividing everything by the
            single global-max gradient — so every fold contributes, not just
            the strongest edge.
        """
        dh, dw = design.shape[:2]
        ph, pw = product.shape[:2]

        # Region of the product under the design.
        y1 = max(0, paste_y); y2 = min(ph, paste_y + dh)
        x1 = max(0, paste_x); x2 = min(pw, paste_x + dw)
        if y2 <= y1 or x2 <= x1:
            return design

        roi = product[y1:y2, x1:x2]
        roi_h, roi_w = roi.shape[:2]

        dy1 = y1 - paste_y; dy2 = dy1 + roi_h
        dx1 = x1 - paste_x; dx2 = dx1 + roi_w
        design_crop = design[dy1:dy2, dx1:dx2]
        if design_crop.size == 0:
            return design

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.float32)

        # Height field: fabric folds are smooth luminance variations. Blur out
        # fine weave noise but keep folds/creases/seams.
        sigma = max(1.0, min(roi_h, roi_w) * 0.03)
        k = int(sigma * 4) | 1
        height = cv2.GaussianBlur(gray, (k, k), sigma)

        # Gradient of the height field = direction fabric pushes the print.
        grad_x = cv2.Sobel(height, cv2.CV_32F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(height, cv2.CV_32F, 0, 1, ksize=5)

        # Local normalisation: divide by a smoothed magnitude so gentle folds
        # far from the strongest edge still displace the design.
        mag = cv2.GaussianBlur(np.sqrt(grad_x ** 2 + grad_y ** 2), (k, k), sigma)
        denom = mag + (mag.mean() + 1e-5)
        dir_x = grad_x / denom
        dir_y = grad_y / denom

        # Amplitude: gentle and capped. A print conforms to fabric by only a
        # few pixels — large values produce a "melted/folded paper" ripple.
        if self.quality == "preview":
            amp = min(3.0, max(1.0, roi_w * 0.005))
        else:
            amp = min(5.0, max(1.5, roi_w * 0.008))

        map_y, map_x = np.meshgrid(
            np.arange(roi_h, dtype=np.float32),
            np.arange(roi_w, dtype=np.float32),
            indexing="ij",
        )
        map_x = np.clip(map_x + dir_x * amp, 0, roi_w - 1).astype(np.float32)
        map_y = np.clip(map_y + dir_y * amp, 0, roi_h - 1).astype(np.float32)

        interp = cv2.INTER_CUBIC if self.quality == "final" else cv2.INTER_LINEAR
        warped = cv2.remap(
            design_crop, map_x, map_y,
            interpolation=interp,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

        result = design.copy()
        result[dy1:dy2, dx1:dx2] = warped
        return result

    def _apply_curvature(self, design: np.ndarray) -> np.ndarray:
        """
        Apply a gentle, SYMMETRIC horizontal cylindrical warp to sell the
        curvature of a rounded surface such as a cap crown or beanie, WITHOUT
        cropping the design's edges.

        Root-cause fix vs. the previous version:
          The old barrel formula ``src_x = c + xs*(1 - comp*xs²)*c`` mapped the
          output's edge columns to ~4% *inside* the source, so the outer ~4%
          of the design on each side was never sampled and was silently
          cropped — shaving the left/right arcs off a round logo.

          This uses the true head-on cylinder projection instead:
              screen  = sin(theta) / sin(theta_max)      (uniform output)
              texture = theta / theta_max                (design coordinate)
          Inverting for a uniform screen gives
              texture = asin(screen · sin(theta_max)) / theta_max
          Because texture(±1) == ±1, the design's extreme left/right columns
          are ALWAYS preserved (no edge loss), while interior columns are
          bulged at the centre and compressed toward the edges — exactly how a
          circular patch wraps a cylinder seen straight on. A circle stays a
          full, clean circle at any position.

        Only horizontal compression is applied (no vertical droop): droop
        shifted edge columns off the canvas and clipped the patch unevenly.
        """
        dh, dw = design.shape[:2]
        if dw < 4 or dh < 4:
            return design

        # theta_max controls how much of the cylinder we wrap around
        # (larger = more pronounced curve). ~0.6 rad ≈ 34°.
        theta_max = 0.60
        sin_tm = float(np.sin(theta_max))

        i = np.arange(dw, dtype=np.float32)
        screen = (2.0 * i / (dw - 1)) - 1.0                       # -1..1 uniform
        texture = np.arcsin(np.clip(screen * sin_tm, -1.0, 1.0)) / theta_max
        src_x = (texture + 1.0) * 0.5 * (dw - 1)                  # 0..dw-1

        map_x = np.tile(src_x, (dh, 1)).astype(np.float32)
        map_y = np.tile(
            np.arange(dh, dtype=np.float32).reshape(-1, 1), (1, dw)
        ).astype(np.float32)

        interp = cv2.INTER_CUBIC if self.quality == "final" else cv2.INTER_LINEAR
        return cv2.remap(
            design, map_x, map_y,
            interpolation=interp,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

    # ────────────────────────────────────────────────────────────────
    # Stage 5: Realistic Blending
    # ────────────────────────────────────────────────────────────────

    def _blend_realistic(
        self,
        product: np.ndarray,
        design: np.ndarray,
        paste_x: int,
        paste_y: int,
    ) -> np.ndarray:
        """
        Composite the design so it looks printed *into* the fabric.

        Root-cause fix vs. the previous version: instead of multiplying by
        luminance normalised to the ROI **mean** (which is ~1 everywhere on an
        even-toned garment and therefore does nothing), we transfer the
        fabric's **local shading** — the ratio of each pixel's luminance to a
        locally-blurred average. Folds/creases (<1) darken the print and
        highlights (>1) brighten it, independent of the garment's base colour,
        so a print reads correctly on white, forest-green or black alike.
        """
        result = product.copy()
        dh, dw = design.shape[:2]
        ph, pw = product.shape[:2]

        y1 = max(0, paste_y); y2 = min(ph, paste_y + dh)
        x1 = max(0, paste_x); x2 = min(pw, paste_x + dw)
        if y2 <= y1 or x2 <= x1:
            return result

        dy1 = y1 - paste_y; dy2 = dy1 + (y2 - y1)
        dx1 = x1 - paste_x; dx2 = dx1 + (x2 - x1)

        design_crop = design[dy1:dy2, dx1:dx2]
        product_roi = product[y1:y2, x1:x2].copy()

        if design_crop.shape[2] == 4:
            alpha = design_crop[:, :, 3].astype(np.float32) / 255.0
            design_bgr = design_crop[:, :, :3].astype(np.float32) / 255.0
        else:
            alpha = np.ones(design_crop.shape[:2], dtype=np.float32)
            design_bgr = design_crop.astype(np.float32) / 255.0

        product_float = product_roi.astype(np.float32) / 255.0
        rh, rw = product_roi.shape[:2]

        # ── Local shading field ──
        gray = cv2.cvtColor(product_roi, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        sigma = max(1.0, min(rh, rw) * 0.06)
        k = int(sigma * 4) | 1
        local_avg = cv2.GaussianBlur(gray, (k, k), sigma)
        # Ratio of actual luminance to local average: 1 = flat, <1 shadow/fold,
        # >1 highlight. This is what makes creases appear on the print.
        shading = gray / (local_avg + 1e-3)
        # Strengthen the effect a touch, then clamp to a sane range. Kept
        # moderate so folds/creases read on the print without crushing it to
        # black or blowing out highlights (which looked artificial before).
        strength = 1.25 if self.quality == "preview" else 1.4
        shading = np.clip(1.0 + (shading - 1.0) * strength, 0.5, 1.65)
        shading_3ch = np.stack([shading] * 3, axis=-1)

        # Apply fabric shading to the (opaque ink) design colour.
        shaded = np.clip(design_bgr * shading_3ch, 0.0, 1.0)

        # ── Fine texture (weave/grain) carried through the print ──
        blur_size = max(3, int(min(rh, rw) * 0.04) | 1)
        product_blurred = cv2.GaussianBlur(product_float, (blur_size, blur_size), 0)
        texture = product_float - product_blurred  # high-frequency detail
        texture_strength = 0.3 if self.quality == "preview" else 0.4
        shaded = np.clip(shaded + texture * texture_strength, 0.0, 1.0)

        # ── Alpha compositing over the original fabric ──
        # Soften alpha edges slightly so the print doesn't have a hard cutout.
        alpha_soft = cv2.GaussianBlur(alpha, (3, 3), 0)
        alpha_3ch = np.stack([alpha_soft] * 3, axis=-1)
        blended = shaded * alpha_3ch + product_float * (1.0 - alpha_3ch)
        blended = np.clip(blended, 0.0, 1.0)

        result[y1:y2, x1:x2] = (blended * 255).astype(np.uint8)
        return result


def render_design_on_product(
    product_image_path: str,
    design_image_path: str,
    print_area: Dict[str, int],
    design_settings: Optional[Dict[str, Any]] = None,
    quality: str = "preview",
    surface: str = "flat",
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    High-level function to render a design onto a product image.

    Args:
        product_image_path: Path to the product photo
        design_image_path: Path to the design artwork
        print_area: Dict with x, y, width, height, rotation keys
        design_settings: User adjustments (scale, rotation, offsetX, offsetY)
        quality: "preview" or "final"
        surface: "flat" or "cap" (applies cylindrical curvature)

    Returns:
        Tuple of (rendered_image, timing_dict)
    """
    # Load images
    product = cv2.imread(product_image_path, cv2.IMREAD_COLOR)
    design = cv2.imread(design_image_path, cv2.IMREAD_UNCHANGED)

    if product is None:
        raise ValueError(f"Could not load product image: {product_image_path}")
    if design is None:
        raise ValueError(f"Could not load design image: {design_image_path}")

    # Ensure design has alpha channel
    if len(design.shape) == 2:
        design = cv2.cvtColor(design, cv2.COLOR_GRAY2BGRA)
    elif design.shape[2] == 3:
        design = cv2.cvtColor(design, cv2.COLOR_BGR2BGRA)

    pipeline = RenderPipeline(quality=quality, surface=surface)
    result = pipeline.render(product, design, print_area, design_settings)

    return result, pipeline.timings
