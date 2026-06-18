"""Claude API recipe extraction service."""

import base64
import json
import logging
import os

import anthropic

logger = logging.getLogger(__name__)

_CLIENT = None

def _get_client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
        _CLIENT = anthropic.Anthropic(api_key=api_key)
    return _CLIENT

_SYSTEM_PROMPT = """You are a recipe extraction assistant. Given recipe content, extract the recipe and return ONLY a valid JSON object with no preamble, explanation, or markdown fences.

The JSON must conform exactly to this schema:
{
  "name": string,
  "source_name": string or null,
  "cuisine": string or null,
  "protein": string or null,
  "prep_time_mins": integer or null,
  "cook_time_mins": integer or null,
  "notes": string or null,
  "ingredients": [
    {"name": string, "quantity": string or null, "sort_order": integer}
  ],
  "steps": [
    {"step_number": integer, "instruction": string}
  ]
}

Rules:
- Return ONLY the JSON object. No text before or after.
- source_name: the website or publication name, not the URL.
- cuisine: single descriptor e.g. "Italian", "Thai", "Mexican". Null if unclear.
- protein: primary protein e.g. "Chicken", "Beef", "Tofu". Null if none.
- prep_time_mins and cook_time_mins: integers in minutes, null if not stated.
- notes: any useful tips, serving suggestions, or variations. Null if none.
- ingredients: every ingredient with sort_order starting at 0.
- steps: every step in order, step_number starting at 1.
"""

def extract_from_text(text: str, source_url: str | None = None) -> dict:
    """
    Extract a recipe from plain text (e.g. cleaned HTML from a URL fetch).

    Args:
        text: Cleaned plain text of the recipe page.
        source_url: Original URL, appended to the prompt for context.

    Returns:
        Parsed recipe dict matching the schema above.

    Raises:
        ValueError: if Claude returns unparseable JSON.
        anthropic.APIError: on API failures.
    """
    user_content = text
    if source_url:
        user_content = f"Source URL: {source_url}\n\n{text}"

    logger.info("Extracting recipe from text (%d chars)", len(text))
    return call_claude(user_content)

def extract_from_document(file_bytes: bytes, media_type: str) -> dict:
    """
    Extract a recipe from an uploaded PDF or image.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        media_type: MIME type e.g. "application/pdf", "image/jpeg".

    Returns:
        Parsed recipe dict matching the schema above.

    Raises:
        ValueError: if Claude returns unparseable JSON or media type unsupported.
        anthropic.APIError: on API failures.
    """
    supported = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"}
    if media_type not in supported:
        raise ValueError(f"Unsupported media type: {media_type}. Supported: {sorted(supported)}")

    encoded = base64.standard_b64encode(file_bytes).decode("utf-8")

    if media_type == "application/pdf":
        content_block = {
            "type": "document",
            "source": {"type": "base64", "media_type": media_type, "data": encoded},
        }
    else:
        content_block = {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": encoded},
        }

    logger.info("Extracting recipe from document (%s, %d bytes)", media_type, len(file_bytes))

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    content_block,
                    {"type": "text", "text": "Extract the recipe from this document."},
                ],
            }
        ],
    )

    return _parse_response(message)

def call_claude(user_text: str) -> dict:
    """Send a text prompt to Claude and return the parsed recipe dict."""
    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_text}],
    )
    return _parse_response(message)

def _parse_response(message) -> dict:
    """Extract JSON from a Claude API response."""
    raw = message.content[0].text.strip()

    # Strip accidental markdown fences if Claude adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Claude returned unparseable JSON: %s\nRaw: %s", e, raw[:500])
        raise ValueError(f"Claude returned unparseable JSON: {e}") from e
