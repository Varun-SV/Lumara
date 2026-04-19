"""
ollama_client.py — Async HTTP client for Ollama (and compatible LM Studio) backends.
Sends vision-capable requests with a base64-encoded image payload.
Exposes: OllamaClient, LumaraLLMError
"""

import base64
import io
import json
import logging
from typing import Any

import httpx
from PIL import Image

logger = logging.getLogger("lumara.ai.ollama")


class LumaraLLMError(Exception):
    """Raised when the LLM backend returns an error or times out."""


class OllamaClient:
    """Async client for the Ollama /api/generate endpoint with vision support."""

    def __init__(
        self,
        host: str,
        port: int,
        model: str,
        timeout_s: int = 30,
    ) -> None:
        self._base_url = f"http://{host}:{port}"
        self._model = model
        self._timeout_s = timeout_s

    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        system: str | None = None,
    ) -> str:
        """Send a generation request and return the raw response string.

        Raises LumaraLLMError on network failure, timeout, or non-200 response.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,  # deterministic for edit suggestions
                "num_predict": 2048,
            },
        }

        if system:
            payload["system"] = system

        if image is not None:
            payload["images"] = [_image_to_base64(image)]

        url = f"{self._base_url}/api/generate"
        logger.debug(f"[OllamaClient] POST {url} model={self._model}")

        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException as e:
            raise LumaraLLMError(
                f"LLM request timed out after {self._timeout_s}s: {e}"
            ) from e
        except httpx.RequestError as e:
            raise LumaraLLMError(f"LLM request failed: {e}") from e

        if resp.status_code != 200:
            raise LumaraLLMError(
                f"LLM backend returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        response_text: str = data.get("response", "")

        if not response_text:
            raise LumaraLLMError("LLM returned an empty response")

        logger.debug(f"[OllamaClient] Response length: {len(response_text)} chars")
        return response_text

    async def list_models(self) -> list[str]:
        """Return a list of locally available models from Ollama."""
        url = f"{self._base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            raise LumaraLLMError(f"Failed to list models: {e}") from e


def _image_to_base64(image: Image.Image, max_dimension: int = 1280) -> str:
    """Resize and base64-encode a PIL image for transmission to Ollama."""
    img = image.copy()
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    if img.mode != "RGB":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
