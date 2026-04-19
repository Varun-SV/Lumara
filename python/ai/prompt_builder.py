"""
prompt_builder.py — Builds structured prompts for the Lumara vision LLM.
Constructs the system prompt and user message for both initial analysis
and natural-language edit command flows.
Exposes: build_analysis_prompt(user_message) -> str, SYSTEM_PROMPT: str
"""

from pathlib import Path

# Load the system prompt from docs/ at import time
_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
_SYSTEM_PROMPT_PATH = _DOCS_DIR / "system_prompt.md"

try:
    SYSTEM_PROMPT: str = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    # Fallback minimal system prompt if docs file is missing
    SYSTEM_PROMPT = (
        "You are an AI photo editor. Analyse the provided image and return a "
        "JSON response with fields: analysis, suggestions, caption, tags. "
        "All output must be valid JSON only."
    )

_INITIAL_ANALYSIS_PROMPT = (
    "Please analyse this photograph. Return your response as a single valid JSON object "
    "with the following top-level keys where applicable: "
    "analysis, suggestions (3–5 items), caption, tags. "
    "Do not include any text outside the JSON object."
)

_EDIT_COMMAND_PREFIX = (
    "The user has issued the following edit command for this photograph: "
)

_EDIT_COMMAND_SUFFIX = (
    "\n\nTranslate this into edit instructions. Return a single valid JSON object "
    "with the key: applied_edits (array). "
    "Use parametric edits where possible; only use code-type edits for pixel-level operations. "
    "Do not include any text outside the JSON object."
)


def build_analysis_prompt(user_message: str | None = None) -> str:
    """Return the user-turn prompt for image analysis or an edit command.

    If user_message is None or empty, builds an initial analysis prompt.
    Otherwise, wraps the user message as an edit command.
    """
    if not user_message or user_message.strip() == "":
        return _INITIAL_ANALYSIS_PROMPT

    return f"{_EDIT_COMMAND_PREFIX}\"{user_message.strip()}\"{_EDIT_COMMAND_SUFFIX}"


def get_system_prompt() -> str:
    """Return the full system prompt string."""
    return SYSTEM_PROMPT
