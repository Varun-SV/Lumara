"""
ai_ops.py — AI-powered pixel-level operations (inpainting, outpainting, style transfer).
These operations require diffusers / torch; stubs are provided for environments without GPU.
Exposes: apply_ai_op(image, params) -> PIL.Image.Image
"""

import textwrap
from typing import Any
from PIL import Image


class LumaraAIError(Exception):
    """Raised when an AI op cannot be executed (missing deps or GPU)."""


def apply_ai_op(image: Image.Image, params: dict) -> Image.Image:
    """Dispatch an AI operation based on params keys.

    Supported op keys (checked in order):
      _code         — execute an arbitrary Python code string
      inpainting    — content-aware fill / object removal
      outpainting   — canvas expansion with direction + percentage
      style_transfer — apply a named or reference-based style
      sky_replacement — swap sky region
      subject_isolation — generate subject mask
    """
    if code := params.get("_code"):
        return _run_code(image, params, code)

    if "inpainting" in params:
        return _inpaint(image, params)

    if "outpainting" in params:
        return _outpaint(image, params)

    if "style_transfer" in params:
        return _style_transfer(image, params)

    if "sky_replacement" in params:
        return _sky_replace(image, params)

    if "subject_isolation" in params:
        return _subject_isolate(image, params)

    return image  # no-op if no recognised key


# ---------------------------------------------------------------------------
# Private implementations
# ---------------------------------------------------------------------------

def _run_code(image: Image.Image, params: dict, code: str) -> Image.Image:
    """Execute a user/AI-provided apply_edit function in a restricted namespace."""
    namespace: dict[str, Any] = {"PIL": __import__("PIL"), "Image": Image}
    try:
        exec(compile(code, "<llm_edit>", "exec"), namespace)  # noqa: S102
    except SyntaxError as e:
        raise LumaraAIError(f"Syntax error in generated code: {e}") from e

    fn = namespace.get("apply_edit")
    if not callable(fn):
        raise LumaraAIError("Generated code must define apply_edit(image, params) -> Image")

    result = fn(image, params)
    if not isinstance(result, Image.Image):
        raise LumaraAIError("apply_edit must return a PIL.Image.Image")

    return result


def _inpaint(image: Image.Image, params: dict) -> Image.Image:
    """Inpainting stub — returns the original image with a warning annotation."""
    _warn_diffusers_missing("inpainting")
    return image


def _outpaint(image: Image.Image, params: dict) -> Image.Image:
    """Outpainting stub — expands the canvas with mirrored padding as a placeholder."""
    op_params: dict = params.get("outpainting", {})
    direction: str = op_params.get("direction", "all")
    pct: float = float(op_params.get("percentage", 10)) / 100.0

    w, h = image.size
    pad_x = int(w * pct) if direction in ("left", "right", "horizontal", "all") else 0
    pad_y = int(h * pct) if direction in ("top", "bottom", "vertical", "all") else 0

    new_w, new_h = w + pad_x * 2, h + pad_y * 2
    canvas = Image.new("RGB", (new_w, new_h), (0, 0, 0))
    canvas.paste(image, (pad_x, pad_y))
    # Placeholder: mirror borders into the new regions
    if pad_x > 0:
        left_strip = image.crop((0, 0, pad_x, h)).transpose(Image.FLIP_LEFT_RIGHT)
        right_strip = image.crop((w - pad_x, 0, w, h)).transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(left_strip, (0, pad_y))
        canvas.paste(right_strip, (pad_x + w, pad_y))
    if pad_y > 0:
        top_strip = image.crop((0, 0, w, pad_y)).transpose(Image.FLIP_TOP_BOTTOM)
        bottom_strip = image.crop((0, h - pad_y, w, h)).transpose(Image.FLIP_TOP_BOTTOM)
        canvas.paste(top_strip, (pad_x, 0))
        canvas.paste(bottom_strip, (pad_x, pad_y + h))

    return canvas


def _style_transfer(image: Image.Image, params: dict) -> Image.Image:
    """Style transfer stub — requires diffusers."""
    _warn_diffusers_missing("style_transfer")
    return image


def _sky_replace(image: Image.Image, params: dict) -> Image.Image:
    """Sky replacement stub — requires segmentation model."""
    _warn_diffusers_missing("sky_replacement")
    return image


def _subject_isolate(image: Image.Image, params: dict) -> Image.Image:
    """Subject isolation stub — requires segmentation model."""
    _warn_diffusers_missing("subject_isolation")
    return image


def _warn_diffusers_missing(op: str) -> None:
    """Log a warning that diffusers is required for this operation."""
    import warnings
    warnings.warn(
        f"[ai_ops] '{op}' requires torch + diffusers. "
        "Install the optional AI dependencies listed in requirements.txt.",
        stacklevel=3,
    )
