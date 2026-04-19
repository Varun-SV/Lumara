"""
basic.py — Basic tonal and presence adjustments for Lumara.
Handles: exposure, contrast, highlights, shadows, whites, blacks,
         clarity, texture, dehaze, vibrance, saturation, vignette.
Exposes: apply_basic(image, params) -> PIL.Image.Image
"""

import math
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def apply_basic(image: Image.Image, params: dict) -> Image.Image:
    """Apply basic tonal/presence adjustments from the edit parameter dict."""
    img = image.convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0

    # --- Exposure (EV stops) ---
    if ev := params.get("exposure", 0):
        arr = arr * (2.0 ** float(ev))

    # --- Contrast ---
    if c := params.get("contrast", 0):
        factor = (259 * (float(c) + 255)) / (255 * (259 - float(c)))
        arr = factor * (arr - 0.5) + 0.5

    # --- Highlights / Shadows (luminosity-aware) ---
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

    if hl := params.get("highlights", 0):
        mask = np.clip((lum - 0.5) * 2.0, 0, 1)[:, :, np.newaxis]
        arr = arr + (float(hl) / 100.0) * 0.3 * mask

    if sh := params.get("shadows", 0):
        mask = np.clip((0.5 - lum) * 2.0, 0, 1)[:, :, np.newaxis]
        arr = arr + (float(sh) / 100.0) * 0.3 * mask

    # --- Whites / Blacks ---
    if w := params.get("whites", 0):
        arr = arr + (float(w) / 100.0) * 0.15 * (arr ** 2)
    if b := params.get("blacks", 0):
        arr = arr + (float(b) / 100.0) * 0.15 * ((1 - arr) ** 2) * -1

    # --- Saturation ---
    if sat := params.get("saturation", 0):
        grey = lum[:, :, np.newaxis]
        arr = grey + (1.0 + float(sat) / 100.0) * (arr - grey)

    # --- Vibrance (selective saturation of muted colours) ---
    if vib := params.get("vibrance", 0):
        sat_map = np.max(arr, axis=2) - np.min(arr, axis=2)
        vibrancy_mask = (1.0 - sat_map)[:, :, np.newaxis]
        grey = lum[:, :, np.newaxis]
        arr = grey + (1.0 + float(vib) / 100.0 * vibrancy_mask) * (arr - grey)

    # --- Clarity (midtone contrast via unsharp mask on L channel) ---
    if cl := params.get("clarity", 0):
        pil_tmp = _arr_to_pil(np.clip(arr, 0, 1))
        blurred = pil_tmp.filter(ImageFilter.GaussianBlur(radius=10))
        b_arr = np.array(blurred, dtype=np.float32) / 255.0
        arr = arr + (float(cl) / 100.0) * 0.5 * (arr - b_arr)

    # --- Texture (fine-detail contrast) ---
    if tx := params.get("texture", 0):
        pil_tmp = _arr_to_pil(np.clip(arr, 0, 1))
        blurred = pil_tmp.filter(ImageFilter.GaussianBlur(radius=3))
        b_arr = np.array(blurred, dtype=np.float32) / 255.0
        arr = arr + (float(tx) / 100.0) * 0.4 * (arr - b_arr)

    # --- Dehaze (increase contrast + saturation in foggy regions) ---
    if dh := params.get("dehaze", 0):
        arr = arr * (1.0 + float(dh) / 200.0) - (float(dh) / 400.0)

    # --- Vignette ---
    if vg := params.get("vignette_amount", 0):
        arr = _apply_vignette(arr, float(vg), params.get("vignette_midpoint", 50))

    arr = np.clip(arr, 0, 1)
    return _arr_to_pil(arr)


def _apply_vignette(arr: np.ndarray, amount: float, midpoint: float) -> np.ndarray:
    """Apply a radial vignette mask to the image array."""
    h, w = arr.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    ys, xs = np.mgrid[0:h, 0:w]
    dist = np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2)
    falloff = midpoint / 100.0
    mask = np.clip(1.0 - np.clip((dist - falloff) / (1.0 - falloff + 1e-6), 0, 1), 0, 1)
    # amount > 0 = darken corners, amount < 0 = lighten corners
    vignette = 1.0 + (amount / 100.0) * (mask - 1.0)
    return arr * vignette[:, :, np.newaxis]


def _arr_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert a float32 [0,1] array to uint8 PIL image."""
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode="RGB")
