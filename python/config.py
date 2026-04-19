"""
config.py — Loads Lumara runtime configuration for the Python sidecar.
Reads from config.json (project root) merged with config.local.json if present.
Exposes: get_config(), LumaraConfig.
"""

import json
import os
from pathlib import Path
from typing import Any


def _find_config_root() -> Path:
    """Walk up from this file's directory to find config.json."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "config.json"
        if candidate.exists():
            return parent
    return here.parent.parent  # fallback: project root


def _merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge patch into base; patch wins on key collision."""
    result = dict(base)
    for key, val in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _merge(result[key], val)
        else:
            result[key] = val
    return result


def _load_raw() -> dict[str, Any]:
    root = _find_config_root()
    with open(root / "config.json") as f:
        cfg: dict[str, Any] = json.load(f)

    local_path = root / "config.local.json"
    if local_path.exists():
        with open(local_path) as f:
            local: dict[str, Any] = json.load(f)
        cfg = _merge(cfg, local)

    # Allow environment variable overrides for the sidecar port
    if port_env := os.environ.get("LUMARA_SIDECAR_PORT"):
        cfg.setdefault("sidecar", {})["port"] = int(port_env)

    return cfg


class LumaraConfig:
    """Typed wrapper around the raw config dict."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self._raw = raw

    # --- Sidecar ---
    @property
    def sidecar_host(self) -> str:
        return self._raw["sidecar"]["host"]

    @property
    def sidecar_port(self) -> int:
        return int(self._raw["sidecar"]["port"])

    @property
    def sidecar_timeout_ms(self) -> int:
        return int(self._raw["sidecar"]["timeout_ms"])

    # --- LLM ---
    @property
    def llm_backend(self) -> str:
        return self._raw["llm"]["backend"]

    @property
    def llm_host(self) -> str:
        return self._raw["llm"]["host"]

    @property
    def llm_port(self) -> int:
        return int(self._raw["llm"]["port"])

    @property
    def llm_model(self) -> str:
        return self._raw["llm"]["model"]

    @property
    def llm_timeout_s(self) -> int:
        return int(self._raw["llm"]["timeout_s"])

    @property
    def llm_max_tokens(self) -> int:
        return int(self._raw["llm"]["max_tokens"])

    # --- Editing ---
    @property
    def batch_tolerance(self) -> float:
        return float(self._raw["editing"]["batch_adjustment_tolerance"])

    @property
    def default_export_quality(self) -> int:
        return int(self._raw["editing"]["default_export_quality"])

    @property
    def default_export_format(self) -> str:
        return self._raw["editing"]["default_export_format"]


_config_instance: LumaraConfig | None = None


def get_config() -> LumaraConfig:
    """Return the singleton config instance, loading it on first call."""
    global _config_instance
    if _config_instance is None:
        _config_instance = LumaraConfig(_load_raw())
    return _config_instance
