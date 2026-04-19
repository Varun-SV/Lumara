"""
response_parser.py — Validates and parses LLM JSON responses for Lumara.
Strips markdown fences, validates required fields, and normalises the structure.
Exposes: parse_llm_response(raw: str) -> dict, LumaraParseError
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger("lumara.ai.parser")

_VALID_TOP_LEVEL_KEYS = {
    "analysis",
    "suggestions",
    "applied_edits",
    "caption",
    "tags",
    "answer",
    "warnings",
}

_VALID_SCENE_TYPES = {
    "portrait", "landscape", "macro", "street",
    "architecture", "product", "abstract", "night",
}

_VALID_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}


class LumaraParseError(Exception):
    """Raised when the LLM response cannot be parsed or is structurally invalid."""


def parse_llm_response(raw: str) -> dict[str, Any]:
    """Parse a raw LLM response string into a validated dict.

    Handles common model quirks:
    - Markdown code fences (```json ... ```)
    - Leading/trailing prose before/after the JSON block
    - Partially-formed responses (returns warnings instead of raising)
    """
    cleaned = _extract_json(raw)

    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"[parser] JSON decode failed: {e}. Raw excerpt: {raw[:200]}")
        return {"warnings": [f"LLM response could not be parsed as JSON: {e}"]}

    if not isinstance(data, dict):
        return {"warnings": ["LLM response was not a JSON object"]}

    # Strip unknown top-level keys (defensive)
    data = {k: v for k, v in data.items() if k in _VALID_TOP_LEVEL_KEYS}

    # Normalise and validate sub-structures
    warnings: list[str] = list(data.get("warnings", []))

    if "analysis" in data:
        data["analysis"], w = _validate_analysis(data["analysis"])
        warnings.extend(w)

    if "suggestions" in data:
        data["suggestions"], w = _validate_suggestions(data["suggestions"])
        warnings.extend(w)

    if "applied_edits" in data:
        data["applied_edits"], w = _validate_applied_edits(data["applied_edits"])
        warnings.extend(w)

    if "tags" in data and not isinstance(data["tags"], list):
        warnings.append("'tags' field is not a list; ignoring")
        del data["tags"]

    if warnings:
        data["warnings"] = warnings

    return data


def _extract_json(text: str) -> str:
    """Extract the JSON portion from a potentially fence-wrapped LLM response."""
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)

    # Find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text.strip()


def _validate_analysis(a: Any) -> tuple[dict, list[str]]:
    """Validate the analysis object; coerce missing fields to safe defaults."""
    warnings: list[str] = []
    if not isinstance(a, dict):
        return {}, ["analysis field is not an object"]

    if scene := a.get("scene_type"):
        if scene not in _VALID_SCENE_TYPES:
            warnings.append(f"Unknown scene_type '{scene}'; keeping as-is")

    if not isinstance(a.get("issues"), list):
        a["issues"] = []

    return a, warnings


def _validate_suggestions(s: Any) -> tuple[list, list[str]]:
    """Validate the suggestions array; remove malformed items."""
    warnings: list[str] = []
    if not isinstance(s, list):
        return [], ["suggestions field is not an array"]

    valid: list[dict] = []
    for i, item in enumerate(s):
        if not isinstance(item, dict):
            warnings.append(f"Suggestion #{i} is not an object; skipped")
            continue
        if item.get("priority") not in _VALID_PRIORITIES:
            item["priority"] = "MEDIUM"
            warnings.append(f"Suggestion #{i} had invalid priority; defaulted to MEDIUM")
        if "id" not in item:
            item["id"] = f"suggestion_{i}"
        if "edit" not in item:
            item["edit"] = {}
        valid.append(item)

    return valid, warnings


def _validate_applied_edits(e: Any) -> tuple[list, list[str]]:
    """Validate the applied_edits array; remove items missing required fields."""
    warnings: list[str] = []
    if not isinstance(e, list):
        return [], ["applied_edits field is not an array"]

    valid: list[dict] = []
    for i, item in enumerate(e):
        if not isinstance(item, dict):
            warnings.append(f"applied_edit #{i} is not an object; skipped")
            continue
        if item.get("type") not in ("parametric", "code"):
            item["type"] = "parametric"
        if "parameters" not in item:
            item["parameters"] = {}
        if "layer_name" not in item:
            item["layer_name"] = f"Edit {i + 1}"
        item.setdefault("reversible", True)
        valid.append(item)

    return valid, warnings
