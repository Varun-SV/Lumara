"""
test_ollama_client.py — Unit tests for OllamaClient and response_parser.
Uses httpx's mock transport to avoid needing a real Ollama backend.
"""

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))

from ai.ollama_client import OllamaClient, LumaraLLMError, _image_to_base64
from ai.response_parser import parse_llm_response, LumaraParseError
from ai.prompt_builder import build_analysis_prompt, get_system_prompt


# ---------------------------------------------------------------------------
# OllamaClient — unit tests with mocked HTTP
# ---------------------------------------------------------------------------

class TestOllamaClient:
    def _make_client(self) -> OllamaClient:
        return OllamaClient(host="127.0.0.1", port=11434, model="llava:latest", timeout_s=5)

    @pytest.mark.asyncio
    async def test_generate_success(self, respx_mock):
        """Should return the response text on a 200 reply."""
        import respx, httpx

        payload = {"response": '{"analysis": {"scene_type": "landscape"}}'}
        respx_mock.post("http://127.0.0.1:11434/api/generate").mock(
            return_value=httpx.Response(200, json=payload)
        )

        client = self._make_client()
        result = await client.generate("Analyse this image")
        assert "landscape" in result

    @pytest.mark.asyncio
    async def test_generate_timeout_raises(self, respx_mock):
        """Should raise LumaraLLMError on timeout."""
        import respx, httpx

        respx_mock.post("http://127.0.0.1:11434/api/generate").mock(
            side_effect=httpx.TimeoutException("timed out")
        )

        client = self._make_client()
        with pytest.raises(LumaraLLMError, match="timed out"):
            await client.generate("Analyse this image")

    @pytest.mark.asyncio
    async def test_generate_non_200_raises(self, respx_mock):
        """Should raise LumaraLLMError on non-200 HTTP status."""
        import respx, httpx

        respx_mock.post("http://127.0.0.1:11434/api/generate").mock(
            return_value=httpx.Response(503, text="Service unavailable")
        )

        client = self._make_client()
        with pytest.raises(LumaraLLMError, match="HTTP 503"):
            await client.generate("Analyse this image")

    @pytest.mark.asyncio
    async def test_generate_empty_response_raises(self, respx_mock):
        """Should raise LumaraLLMError if response field is empty."""
        import respx, httpx

        respx_mock.post("http://127.0.0.1:11434/api/generate").mock(
            return_value=httpx.Response(200, json={"response": ""})
        )

        client = self._make_client()
        with pytest.raises(LumaraLLMError, match="empty"):
            await client.generate("Analyse this image")

    def test_image_to_base64_produces_string(self):
        """_image_to_base64 should return a non-empty base64 string."""
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        result = _image_to_base64(img)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_image_to_base64_downsamples_large_image(self):
        """Large images should be resized before encoding."""
        large_img = Image.new("RGB", (4000, 3000), (200, 100, 50))
        result_large = _image_to_base64(large_img, max_dimension=1280)
        small_img = Image.new("RGB", (200, 150), (200, 100, 50))
        result_small = _image_to_base64(small_img, max_dimension=1280)
        # The large image base64 should be roughly comparable to the small one
        # (both get downsampled / are low-entropy), not orders of magnitude larger
        assert len(result_large) < len(result_small) * 50


# ---------------------------------------------------------------------------
# response_parser tests
# ---------------------------------------------------------------------------

class TestResponseParser:
    def test_valid_full_response(self):
        raw = json.dumps({
            "analysis": {
                "scene_type": "landscape",
                "lighting": "soft morning light",
                "issues": [],
                "mood": "serene",
                "composition_notes": "rule of thirds"
            },
            "suggestions": [
                {
                    "id": "boost_shadows",
                    "label": "Lift shadows",
                    "reason": "Subject is underexposed.",
                    "priority": "HIGH",
                    "edit": {"shadows": 40}
                }
            ],
            "caption": "A misty mountain landscape at dawn.",
            "tags": ["landscape", "mist", "mountains"]
        })
        result = parse_llm_response(raw)
        assert result["analysis"]["scene_type"] == "landscape"
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["priority"] == "HIGH"

    def test_strips_markdown_fences(self):
        raw = "```json\n{\"answer\": \"The photo is overexposed.\"}\n```"
        result = parse_llm_response(raw)
        assert result["answer"] == "The photo is overexposed."

    def test_invalid_json_returns_warning(self):
        result = parse_llm_response("not json at all {broken")
        assert "warnings" in result
        assert any("JSON" in w for w in result["warnings"])

    def test_invalid_priority_defaulted(self):
        raw = json.dumps({
            "suggestions": [
                {"id": "x", "label": "Test", "reason": "r", "priority": "EXTREME", "edit": {}}
            ]
        })
        result = parse_llm_response(raw)
        assert result["suggestions"][0]["priority"] == "MEDIUM"

    def test_unknown_top_level_keys_stripped(self):
        raw = json.dumps({"answer": "ok", "_internal_debug": "secret"})
        result = parse_llm_response(raw)
        assert "_internal_debug" not in result

    def test_applied_edits_defaults_reversible(self):
        raw = json.dumps({
            "applied_edits": [
                {"type": "parametric", "description": "Test", "parameters": {"exposure": 0.5}, "layer_name": "L1"}
            ]
        })
        result = parse_llm_response(raw)
        assert result["applied_edits"][0]["reversible"] is True


# ---------------------------------------------------------------------------
# prompt_builder tests
# ---------------------------------------------------------------------------

class TestPromptBuilder:
    def test_no_message_returns_analysis_prompt(self):
        prompt = build_analysis_prompt(None)
        assert "analyse" in prompt.lower() or "analysis" in prompt.lower()

    def test_empty_message_returns_analysis_prompt(self):
        prompt = build_analysis_prompt("")
        assert "JSON" in prompt

    def test_user_message_wrapped_correctly(self):
        prompt = build_analysis_prompt("Make it moodier")
        assert "Make it moodier" in prompt
        assert "applied_edits" in prompt

    def test_system_prompt_is_string(self):
        sp = get_system_prompt()
        assert isinstance(sp, str)
        assert len(sp) > 100
