"""
exporter.py — Image export and preview rendering utilities.
Handles writing the final processed image to disk in JPEG, PNG, TIFF, or WEBP.
Exposes: export_image(image, output_path, format, quality), render_preview(image) -> bytes
"""

import io
from pathlib import Path
from PIL import Image

_FORMAT_ALIASES: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "tiff": "TIFF",
    "tif": "TIFF",
}


def export_image(
    image: Image.Image,
    output_path: str,
    fmt: str = "jpeg",
    quality: int = 92,
) -> None:
    """Write a processed image to disk.

    Never overwrites the original source file — the caller must pass a
    distinct output_path (e.g. filename_export.jpg).
    """
    path = Path(output_path)
    pil_format = _FORMAT_ALIASES.get(fmt.lower(), fmt.upper())

    save_kwargs: dict = {}
    if pil_format == "JPEG":
        save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
    elif pil_format == "WEBP":
        save_kwargs = {"quality": quality, "method": 4}
    elif pil_format == "TIFF":
        save_kwargs = {"compression": "lzw"}

    image.save(str(path), format=pil_format, **save_kwargs)


def render_preview(image: Image.Image, max_dimension: int = 2400, quality: int = 85) -> bytes:
    """Return a JPEG-encoded preview as raw bytes, downsampled if needed."""
    preview = image.copy()
    if max(preview.size) > max_dimension:
        preview.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    buf = io.BytesIO()
    preview.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()
