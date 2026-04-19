"""
portrait.py — Portrait-specific retouching operations.
Handles: skin_smoothing, eye_enhancement, teeth_whitening, face_brightness.
Note: blemish_removal requires face detection (optional OpenCV cascade).
Exposes: apply_portrait(image, params) -> PIL.Image.Image
"""

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def apply_portrait(image: Image.Image, params: dict) -> Image.Image:
    """Apply portrait retouching adjustments from the 'portrait' key in params."""
    portrait: dict = params.get("portrait", {})
    if not portrait:
        return image

    img = image.convert("RGB")

    # --- Skin smoothing (frequency separation approximation) ---
    if ss := portrait.get("skin_smoothing", 0):
        img = _skin_smooth(img, float(ss))

    # --- Face brightness (gentle overall brightness lift) ---
    if fb := portrait.get("face_brightness", 0):
        enhancer = ImageEnhance.Brightness(img)
        # Face brightness range: -50 to +50 → factor 0.5 to 1.5
        factor = 1.0 + float(fb) / 100.0
        img = enhancer.enhance(max(0.5, min(factor, 1.5)))

    # --- Eye enhancement (local contrast boost — placeholder, no face detection) ---
    if ee := portrait.get("eye_enhancement", 0):
        img = _enhance_eyes(img, float(ee))

    # --- Teeth whitening (desaturate + brighten yellow/warm tones) ---
    if tw := portrait.get("teeth_whitening", 0):
        img = _whiten_teeth(img, float(tw))

    return img


def _skin_smooth(image: Image.Image, strength: float) -> Image.Image:
    """Frequency-separation skin smoothing: blur low frequencies, preserve details."""
    strength_norm = strength / 100.0

    # Low-frequency layer (strong blur)
    radius = 3.0 + strength_norm * 5.0
    low_freq = image.filter(ImageFilter.GaussianBlur(radius=radius))
    low_arr = np.array(low_freq, dtype=np.float32)
    orig_arr = np.array(image, dtype=np.float32)

    # Blend original with low-freq by strength
    blended = orig_arr + (low_arr - orig_arr) * strength_norm * 0.7
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")


def _enhance_eyes(image: Image.Image, strength: float) -> Image.Image:
    """Increase overall micro-contrast (placeholder for true eye-targeted enhancement)."""
    strength_norm = strength / 100.0
    arr = np.array(image, dtype=np.float32) / 255.0
    blurred = np.array(image.filter(ImageFilter.GaussianBlur(radius=1.5)), dtype=np.float32) / 255.0
    sharpened = arr + (arr - blurred) * strength_norm * 0.5
    return Image.fromarray((np.clip(sharpened, 0, 1) * 255).astype(np.uint8), mode="RGB")


def _whiten_teeth(image: Image.Image, strength: float) -> Image.Image:
    """Desaturate and brighten warm/yellow tones (approximate teeth whitening)."""
    strength_norm = strength / 100.0
    arr = np.array(image, dtype=np.float32) / 255.0

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Identify yellowish pixels: high R+G, low B
    yellow_mask = np.clip((r + g - 2 * b) / 2.0, 0, 1)

    # Desaturate towards grey
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    grey = lum[:, :, np.newaxis]
    desaturation = yellow_mask[:, :, np.newaxis] * strength_norm * 0.5
    arr_out = arr + desaturation * (grey - arr)

    # Slight brightening of identified region
    brightness_boost = yellow_mask[:, :, np.newaxis] * strength_norm * 0.1
    arr_out = arr_out + brightness_boost

    return Image.fromarray((np.clip(arr_out, 0, 1) * 255).astype(np.uint8), mode="RGB")
