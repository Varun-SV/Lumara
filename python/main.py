"""
main.py — FastAPI entry point for the Lumara Python image-processing sidecar.
Routes: /health, /image/load, /image/apply, /sidecar/load, /sidecar/save, /llm/analyse.
Exposes: FastAPI app instance (app).
"""

import base64
import io
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

from config import get_config
from formats.loader import load_image_file
from formats.exporter import render_preview
from processors.basic import apply_basic
from processors.whitebalance import apply_white_balance
from processors.hsl import apply_hsl
from processors.detail import apply_detail
from processors.geometry import apply_geometry
from processors.portrait import apply_portrait
from processors.ai_ops import apply_ai_op
from ai.ollama_client import OllamaClient
from ai.prompt_builder import build_analysis_prompt
from ai.response_parser import parse_llm_response

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("lumara.sidecar")

app = FastAPI(title="Lumara Sidecar", version="0.1.0")

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class LoadImageRequest(BaseModel):
    file_path: str


class ApplyEditsRequest(BaseModel):
    image_path: str
    edit_stack: list[dict]
    output_format: str | None = None
    output_quality: int | None = None


class SidecarLoadRequest(BaseModel):
    file_path: str


class SidecarSaveRequest(BaseModel):
    file_path: str
    edit_stack: list[dict]


class LLMAnalysisRequest(BaseModel):
    image_path: str
    user_message: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROCESSOR_MAP = {
    "exposure": apply_basic,
    "contrast": apply_basic,
    "highlights": apply_basic,
    "shadows": apply_basic,
    "whites": apply_basic,
    "blacks": apply_basic,
    "clarity": apply_basic,
    "texture": apply_basic,
    "dehaze": apply_basic,
    "vibrance": apply_basic,
    "saturation": apply_basic,
    "temperature": apply_white_balance,
    "tint": apply_white_balance,
    "tone_curve": apply_white_balance,
    "hsl": apply_hsl,
    "sharpening_amount": apply_detail,
    "noise_luminance": apply_detail,
    "noise_color": apply_detail,
    "vignette_amount": apply_basic,
    "crop_aspect": apply_geometry,
    "straighten_angle": apply_geometry,
    "portrait": apply_portrait,
}

SIDECAR_VERSION = 1


def _image_to_data_url(image: Image.Image, quality: int = 85) -> str:
    """Convert a PIL image to a base64 PNG data URL for the frontend preview."""
    buf = io.BytesIO()
    # Use JPEG for previews (much smaller), PNG for lossless
    image.save(buf, format="JPEG", quality=quality, optimize=True)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def _sidecar_path(image_path: str) -> Path:
    """Return the .lumara.json path for a given source file."""
    p = Path(image_path)
    return p.parent / f"{p.stem}.lumara.json"


def _apply_edit_layer(image: Image.Image, layer: dict) -> tuple[Image.Image, list[str]]:
    """Apply a single edit layer dict to an image; returns (result, warnings)."""
    warnings: list[str] = []
    params: dict = layer.get("parameters", {})
    edit_type: str = layer.get("type", "parametric")

    if edit_type == "code":
        code_str: str = layer.get("code", "")
        if code_str:
            try:
                image = apply_ai_op(image, {"_code": code_str, **params})
            except Exception as e:
                warnings.append(f"Code edit '{layer.get('layer_name')}' failed: {e}")
        return image, warnings

    # Parametric: group params by processor
    visited_processors: set = set()
    for key in params:
        processor_fn = PROCESSOR_MAP.get(key)
        if processor_fn and processor_fn not in visited_processors:
            visited_processors.add(processor_fn)
            try:
                image = processor_fn(image, params)
            except Exception as e:
                warnings.append(f"Processor {processor_fn.__name__} failed: {e}")

    return image, warnings


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check() -> dict:
    """Liveness probe — returns 200 when the sidecar is ready."""
    return {"status": "ok", "version": "0.1.0"}


@app.post("/image/load")
def load_image(req: LoadImageRequest) -> JSONResponse:
    """Decode and return image metadata + base64 preview."""
    try:
        image, meta = load_image_file(req.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    preview_url = _image_to_data_url(image)

    return JSONResponse({
        "id": str(uuid.uuid4()),
        "file_path": req.file_path,
        "file_name": Path(req.file_path).name,
        "format": meta["format"],
        "width_px": image.width,
        "height_px": image.height,
        "preview_data_url": preview_url,
        "analysis": None,
        "caption": None,
        "tags": None,
    })


@app.post("/image/apply")
def apply_edits(req: ApplyEditsRequest) -> JSONResponse:
    """Apply an edit stack to the source image and return an updated preview."""
    try:
        image, _ = load_image_file(req.image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image load failed: {e}")

    all_warnings: list[str] = []
    for layer in req.edit_stack:
        image, layer_warnings = _apply_edit_layer(image, layer)
        all_warnings.extend(layer_warnings)

    quality = req.output_quality or get_config().default_export_quality
    preview_url = _image_to_data_url(image, quality=quality)

    return JSONResponse({
        "preview_data_url": preview_url,
        "warnings": all_warnings,
    })


@app.post("/sidecar/load")
def load_sidecar(req: SidecarLoadRequest) -> JSONResponse:
    """Load a .lumara.json sidecar if it exists alongside the source file."""
    path = _sidecar_path(req.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="No sidecar found")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sidecar parse error: {e}")

    return JSONResponse(data)


@app.post("/sidecar/save")
def save_sidecar(req: SidecarSaveRequest) -> JSONResponse:
    """Persist the edit stack to a .lumara.json sidecar next to the source file."""
    path = _sidecar_path(req.file_path)
    now = datetime.now(timezone.utc).isoformat()

    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    sidecar = {
        "version": SIDECAR_VERSION,
        "source_file": req.file_path,
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "edit_stack": req.edit_stack,
    }

    path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True})


@app.post("/llm/analyse")
async def llm_analyse(req: LLMAnalysisRequest) -> JSONResponse:
    """Send the image + optional user message to the local LLM and return parsed response."""
    cfg = get_config()
    client = OllamaClient(
        host=cfg.llm_host,
        port=cfg.llm_port,
        model=cfg.llm_model,
        timeout_s=cfg.llm_timeout_s,
    )

    try:
        image, _ = load_image_file(req.image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image load failed: {e}")

    prompt = build_analysis_prompt(user_message=req.user_message)

    raw_response = await client.generate(prompt=prompt, image=image)
    parsed = parse_llm_response(raw_response)

    return JSONResponse(parsed)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cfg = get_config()
    logger.info(f"Starting Lumara sidecar on {cfg.sidecar_host}:{cfg.sidecar_port}")
    uvicorn.run(
        "main:app",
        host=cfg.sidecar_host,
        port=cfg.sidecar_port,
        log_level="info",
        reload=False,
    )
