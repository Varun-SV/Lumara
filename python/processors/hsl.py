"""
hsl.py — Per-colour-band HSL adjustments (Hue, Saturation, Luminance).
Supports all 8 bands: red, orange, yellow, green, aqua, blue, purple, magenta.
Exposes: apply_hsl(image, params) -> PIL.Image.Image
"""

import numpy as np
from PIL import Image

# Hue range centres (degrees in [0, 360)) for each named band
_BAND_CENTRES: dict[str, float] = {
    "red":     0.0,
    "orange":  30.0,
    "yellow":  60.0,
    "green":   120.0,
    "aqua":    180.0,
    "blue":    210.0,
    "purple":  270.0,
    "magenta": 330.0,
}
_BAND_WIDTH = 40.0  # degrees on each side of the centre


def apply_hsl(image: Image.Image, params: dict) -> Image.Image:
    """Apply per-band HSL adjustments from the 'hsl' key in params."""
    hsl_params: dict = params.get("hsl", {})
    if not hsl_params:
        return image

    img = image.convert("RGB")
    arr_rgb = np.array(img, dtype=np.float32) / 255.0

    # Convert to HSV for manipulation
    arr_hsv = _rgb_to_hsv(arr_rgb)
    h, s, v = arr_hsv[:, :, 0], arr_hsv[:, :, 1], arr_hsv[:, :, 2]

    for band_name, adjustments in hsl_params.items():
        if band_name not in _BAND_CENTRES:
            continue
        centre = _BAND_CENTRES[band_name]
        mask = _band_mask(h, centre)

        if hue_shift := adjustments.get("hue", 0):
            h = h + (float(hue_shift) / 360.0) * mask

        if sat_shift := adjustments.get("saturation", 0):
            s = np.clip(s + (float(sat_shift) / 100.0) * mask, 0, 1)

        if lum_shift := adjustments.get("luminance", 0):
            v = np.clip(v + (float(lum_shift) / 100.0) * mask, 0, 1)

    # Normalise hue back into [0, 1)
    h = h % 1.0

    arr_hsv = np.stack([h, s, v], axis=2)
    arr_rgb_out = _hsv_to_rgb(arr_hsv)
    return Image.fromarray((np.clip(arr_rgb_out, 0, 1) * 255).astype(np.uint8), mode="RGB")


def _band_mask(h_channel: np.ndarray, centre_deg: float) -> np.ndarray:
    """Return a soft mask [0, 1] for pixels whose hue falls in the named band."""
    centre = centre_deg / 360.0
    width = _BAND_WIDTH / 360.0
    # Circular distance
    dist = np.abs(h_channel - centre)
    dist = np.minimum(dist, 1.0 - dist)  # wrap around
    mask = np.clip(1.0 - dist / width, 0, 1)
    return mask


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """Convert an RGB float32 array to HSV float32 array (all channels in [0, 1])."""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    delta = maxc - minc

    s = np.where(maxc != 0, delta / maxc, 0.0)
    v = maxc

    h = np.zeros_like(r)
    mask_r = (maxc == r) & (delta != 0)
    mask_g = (maxc == g) & (delta != 0)
    mask_b = (maxc == b) & (delta != 0)

    h[mask_r] = ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6
    h[mask_g] = ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2
    h[mask_b] = ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4

    h = (h / 6.0) % 1.0
    return np.stack([h, s, v], axis=2)


def _hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    """Convert an HSV float32 array back to RGB float32."""
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    i = (h * 6.0).astype(np.int32)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i6 = i % 6

    r = np.select([i6 == 0, i6 == 1, i6 == 2, i6 == 3, i6 == 4, i6 == 5], [v, q, p, p, t, v])
    g = np.select([i6 == 0, i6 == 1, i6 == 2, i6 == 3, i6 == 4, i6 == 5], [t, v, v, q, p, p])
    b = np.select([i6 == 0, i6 == 1, i6 == 2, i6 == 3, i6 == 4, i6 == 5], [p, p, t, v, v, q])

    return np.stack([r, g, b], axis=2)
