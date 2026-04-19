"""
whitebalance.py — White balance and tone curve adjustments.
Handles: temperature (relative shift), tint, tone_curve per channel.
Exposes: apply_white_balance(image, params) -> PIL.Image.Image
"""

import numpy as np
from PIL import Image


def apply_white_balance(image: Image.Image, params: dict) -> Image.Image:
    """Apply white balance (temperature/tint) and tone curve adjustments."""
    img = image.convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0

    # --- Temperature (relative shift: -100 cool → +100 warm) ---
    if temp := params.get("temperature", 0):
        shift = float(temp) / 100.0
        arr[:, :, 0] = np.clip(arr[:, :, 0] + shift * 0.10, 0, 1)   # red
        arr[:, :, 2] = np.clip(arr[:, :, 2] - shift * 0.10, 0, 1)   # blue

    # --- Tint (-150 green → +150 magenta) ---
    if tint := params.get("tint", 0):
        shift = float(tint) / 150.0
        arr[:, :, 1] = np.clip(arr[:, :, 1] - shift * 0.07, 0, 1)   # green channel

    # --- Tone curve ---
    if tc := params.get("tone_curve"):
        if luma_pts := tc.get("luma"):
            lut = _build_lut(luma_pts)
            for c in range(3):
                arr[:, :, c] = _apply_lut(arr[:, :, c], lut)
        for ch_idx, ch_key in enumerate(["red", "green", "blue"]):
            if pts := tc.get(ch_key):
                lut = _build_lut(pts)
                arr[:, :, ch_idx] = _apply_lut(arr[:, :, ch_idx], lut)

    arr = np.clip(arr, 0, 1)
    return Image.fromarray((arr * 255).astype(np.uint8), mode="RGB")


def _build_lut(points: list[list[float]]) -> np.ndarray:
    """Build a 256-entry LUT from a list of [input, output] control points (0–255 scale)."""
    pts = sorted(points, key=lambda p: p[0])
    xs = np.array([p[0] for p in pts], dtype=np.float32)
    ys = np.array([p[1] for p in pts], dtype=np.float32)
    lut = np.interp(np.arange(256, dtype=np.float32), xs, ys)
    return lut / 255.0


def _apply_lut(channel: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Apply a 256-entry float LUT to a float32 channel array."""
    indices = np.clip((channel * 255).astype(np.int32), 0, 255)
    return lut[indices]
