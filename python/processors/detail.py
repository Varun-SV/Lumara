"""
detail.py — Sharpening and noise reduction processors.
Handles: sharpening_amount / sharpening_radius / sharpening_masking,
         noise_luminance, noise_color.
Exposes: apply_detail(image, params) -> PIL.Image.Image
"""

import numpy as np
from PIL import Image, ImageFilter


def apply_detail(image: Image.Image, params: dict) -> Image.Image:
    """Apply sharpening and noise reduction adjustments."""
    img = image.convert("RGB")

    # --- Sharpening ---
    amount = float(params.get("sharpening_amount", 0))
    if amount > 0:
        radius = float(params.get("sharpening_radius", 1.0))
        masking = float(params.get("sharpening_masking", 0))
        img = _sharpen(img, amount, radius, masking)

    # --- Luminance noise reduction ---
    nr_lum = float(params.get("noise_luminance", 0))
    nr_col = float(params.get("noise_color", 0))
    if nr_lum > 0 or nr_col > 0:
        img = _noise_reduce(img, nr_lum, nr_col)

    return img


def _sharpen(
    image: Image.Image,
    amount: float,
    radius: float,
    masking: float,
) -> Image.Image:
    """Unsharp-mask-based sharpening with edge masking."""
    arr = np.array(image, dtype=np.float32)

    # Blur radius scales with the sharpening_radius parameter
    blurred = image.filter(ImageFilter.GaussianBlur(radius=radius))
    b_arr = np.array(blurred, dtype=np.float32)
    detail = arr - b_arr

    # Edge mask: apply sharpening more strongly where edges exist
    if masking > 0:
        grey = Image.fromarray(arr.astype(np.uint8)).convert("L")
        edges = np.array(grey.filter(ImageFilter.FIND_EDGES), dtype=np.float32) / 255.0
        # Mask threshold — higher masking = only strongest edges are sharpened
        threshold = masking / 100.0
        mask = np.clip((edges - threshold) / (1.0 - threshold + 1e-6), 0, 1)
        mask = mask[:, :, np.newaxis]
    else:
        mask = 1.0

    strength = amount / 150.0  # normalise to [0, 1]
    sharpened = arr + detail * strength * mask
    return Image.fromarray(np.clip(sharpened, 0, 255).astype(np.uint8), mode="RGB")


def _noise_reduce(image: Image.Image, lum_strength: float, col_strength: float) -> Image.Image:
    """Simple Gaussian-based noise reduction. For production, a BM3D/NLM approach is preferred."""
    arr = np.array(image, dtype=np.float32)

    if lum_strength > 0:
        # Apply mild Gaussian blur scaled by strength
        radius = lum_strength / 100.0 * 2.5
        blurred = image.filter(ImageFilter.GaussianBlur(radius=radius))
        b_arr = np.array(blurred, dtype=np.float32)
        # Blend original with blurred by strength
        blend = lum_strength / 100.0
        arr = arr * (1 - blend) + b_arr * blend

    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")

    if col_strength > 0:
        # Reduce colour noise by blurring in a/b channels of Lab space
        lab = result.convert("LAB")
        lab_arr = np.array(lab, dtype=np.float32)
        radius = col_strength / 100.0 * 3.0
        for c in [1, 2]:  # a and b channels
            chan = Image.fromarray(lab_arr[:, :, c].astype(np.uint8))
            blurred = chan.filter(ImageFilter.GaussianBlur(radius=radius))
            lab_arr[:, :, c] = np.array(blurred, dtype=np.float32)
        result = Image.fromarray(lab_arr.astype(np.uint8), mode="LAB").convert("RGB")

    return result
