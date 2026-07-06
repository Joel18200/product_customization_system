# Rendering Pipeline — Technical Documentation

## Overview

The rendering engine transforms a flat 2D design image into a realistic product mockup where the design appears to be actually printed on the fabric, following wrinkles, folds, and natural lighting.

## Pipeline Stages

### Stage 1: Validation & Preparation

- Ensure product image is BGR (3-channel)
- Ensure design image has alpha channel (BGRA, 4-channel)
- Scale down for preview quality (0.5x) to achieve <2s render times
- Full resolution for final renders

### Stage 2: Print Area Placement

**Input:** Flat design image + print area coordinates + user settings

**Process:**
1. Calculate target dimensions to fit within print area (90% by default)
2. Preserve aspect ratio
3. Apply user scale factor (0.1 - 1.0)
4. Apply user rotation via `cv2.getRotationMatrix2D` + `cv2.warpAffine`
5. Apply user position offsets (X, Y)
6. Center within print area + offset
7. Clamp to print area boundaries

**Output:** Positioned design + paste coordinates

### Stage 3: Perspective Detection & Transform

**Goal:** Make the design follow the product's camera angle and surface tilt.

**Algorithm:**
1. Extract ROI (Region of Interest) around the print area with 15% padding
2. Convert to grayscale and apply Gaussian blur
3. Run Canny edge detection (thresholds: 30, 100)
4. Dilate edges to connect nearby contours
5. Find contours and filter for quadrilateral approximations
6. If a valid quad is found (area > 10% of ROI):
   - Order points (TL, TR, BR, BL)
   - Compute homography matrix via `cv2.findHomography`
   - Apply `cv2.warpPerspective` to the design
7. Fallback: Compute subtle perspective based on print area position relative to image center

**Key functions:** `cv2.Canny`, `cv2.findContours`, `cv2.approxPolyDP`, `cv2.findHomography`, `cv2.warpPerspective`

### Stage 4: Fabric Conformation (Displacement Mapping)

**Goal:** Warp the design to follow fabric wrinkles, folds, and curves.

**Algorithm:**
1. Extract the product image region under the design placement
2. Convert to grayscale (float32)
3. Apply Gaussian blur to focus on macro wrinkle patterns
4. Compute Sobel gradients in X and Y directions (ksize=5)
5. Normalize gradients to displacement range:
   - Preview: max ±3 pixels displacement
   - Final: max ±6 pixels displacement
6. Apply bilateral filter for smooth, edge-preserving displacement
7. Create mesh grid of pixel coordinates
8. Add displacement offsets to mesh
9. Apply `cv2.remap` with bilinear interpolation

**Key insight:** Wrinkles appear as high-gradient regions in the grayscale image. By using Sobel gradients as displacement vectors, design pixels shift to follow these wrinkle contours naturally.

**Key functions:** `cv2.Sobel`, `cv2.bilateralFilter`, `cv2.remap`

### Stage 5: Realistic Blending

**Goal:** Make the design look printed on the fabric, not pasted on top.

**Algorithm:**
1. Extract luminance channel from the product ROI
2. Normalize luminance centered around 1.0
3. **Multiply blend:** `result = design × luminance`
   - Darkens the design where the fabric is dark (shadows, wrinkle valleys)
4. **Overlay blend:** `result = 2×product×design` (dark) or `1-2×(1-product)×(1-design)` (light)
   - Preserves both shadows and highlights
5. **Combine:** 60% multiply + 40% overlay
6. **Texture preservation:**
   - Extract high-frequency texture via `product - gaussian_blur(product)`
   - Add 30-40% of texture detail back to the blended result
7. **Alpha compositing:** Blend with original product using design's alpha channel
8. Convert back to uint8

**Result:** The design inherits the fabric's shadows, wrinkles, and texture grain, creating a photorealistic effect.

## Performance

| Quality | Resolution | Target Time | Displacement | Texture |
|---------|-----------|-------------|--------------|---------|
| Preview | 0.5x | < 2 seconds | ±3px | 30% |
| Final | 1.0x | < 5 seconds | ±6px | 40% |

## Caching

Rendered results are cached in Redis with a key derived from:
- Product view ID
- Design upload ID
- Design settings (scale, rotation, offset)
- Quality level

TTL: 1 hour (preview), 24 hours (final render)
