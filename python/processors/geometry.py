"""
geometry.py — Geometric transformations: crop, straighten, perspective correction.
Exposes: apply_geometry(image, params) -> PIL.Image.Image
"""

import numpy as np
from PIL import Image


_ASPECT_RATIOS: dict[str, tuple[float, float] | None] = {
    "original": None,
    "1:1":      (1.0, 1.0),
    "4:3":      (4.0, 3.0),
    "16:9":     (16.0, 9.0),
    "3:2":      (3.0, 2.0),
    "freeform": None,
}


def apply_geometry(image: Image.Image, params: dict) -> Image.Image:
    """Apply crop, straighten, and perspective correction to the image."""
    img = image.convert("RGB")

    # --- Straighten (rotate) ---
    if angle := params.get("straighten_angle", 0):
        img = _straighten(img, float(angle))

    # --- Crop to aspect ratio ---
    if aspect_key := params.get("crop_aspect"):
        ratio = _ASPECT_RATIOS.get(aspect_key)
        if ratio is not None:
            img = _crop_to_aspect(img, ratio[0], ratio[1])

    return img


def _straighten(image: Image.Image, angle: float) -> Image.Image:
    """Rotate the image by `angle` degrees and crop to eliminate black borders."""
    if angle == 0:
        return image

    rotated = image.rotate(-angle, expand=True, resample=Image.BICUBIC)

    # Compute the largest centred crop that fits inside the rotated canvas
    w, h = image.size
    rw, rh = rotated.size
    angle_rad = abs(angle) * np.pi / 180.0

    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    # Largest axis-aligned rectangle inside a rotated rectangle
    if w * sin_a > h * cos_a:
        crop_w = h / (2 * sin_a) if sin_a != 0 else w
        crop_h = crop_w * h / w
    else:
        crop_h = w / (2 * sin_a) if sin_a != 0 else h
        crop_w = crop_h * w / h

    crop_w = min(int(crop_w), rw)
    crop_h = min(int(crop_h), rh)

    left = (rw - crop_w) // 2
    top = (rh - crop_h) // 2
    return rotated.crop((left, top, left + crop_w, top + crop_h))


def _crop_to_aspect(image: Image.Image, ar_w: float, ar_h: float) -> Image.Image:
    """Centre-crop the image to match the requested aspect ratio."""
    w, h = image.size
    target_ratio = ar_w / ar_h
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.001:
        return image

    if current_ratio > target_ratio:
        # Image is too wide — crop width
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        return image.crop((left, 0, left + new_w, h))
    else:
        # Image is too tall — crop height
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        return image.crop((0, top, w, top + new_h))
