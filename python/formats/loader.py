"""
loader.py — Image loading and decoding for all supported formats.
Handles RAW formats via rawpy and standard formats via Pillow.
Exposes: load_image_file(path) -> tuple[PIL.Image.Image, dict]
"""

from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image

_RAW_EXTENSIONS = {".cr2", ".nef", ".arw", ".dng", ".rw2", ".orf"}
_STANDARD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".heif", ".heic"}


def load_image_file(file_path: str) -> tuple[Image.Image, dict[str, Any]]:
    """Load an image from disk and return a PIL Image plus a metadata dict.

    For RAW files, rawpy is used to demosaic into a 16-bit linear image
    which is then tone-mapped to 8-bit sRGB.
    For standard files, Pillow handles the decode.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {file_path}")

    ext = path.suffix.lower()

    if ext in _RAW_EXTENSIONS:
        return _load_raw(path)
    elif ext in _STANDARD_EXTENSIONS:
        return _load_standard(path)
    else:
        # Attempt Pillow as a fallback for unknown extensions
        return _load_standard(path)


def _load_raw(path: Path) -> tuple[Image.Image, dict[str, Any]]:
    """Decode a RAW file using rawpy and return an 8-bit sRGB PIL image."""
    try:
        import rawpy
    except ImportError as e:
        raise ImportError(
            "rawpy is required for RAW file support. Install with: pip install rawpy"
        ) from e

    with rawpy.imread(str(path)) as raw:
        # Use camera white balance, auto-bright, sRGB output
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=False,
            output_bps=8,
            output_color=rawpy.ColorSpace.sRGB,
        )

    image = Image.fromarray(rgb, mode="RGB")
    meta: dict[str, Any] = {"format": path.suffix.upper().lstrip(".")}
    return image, meta


def _load_standard(path: Path) -> tuple[Image.Image, dict[str, Any]]:
    """Load a standard image format with Pillow and normalise to RGB."""
    image = Image.open(str(path))

    # Normalise to RGB (drop alpha, convert palette modes, etc.)
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    meta: dict[str, Any] = {"format": image.format or path.suffix.upper().lstrip(".")}
    return image, meta
