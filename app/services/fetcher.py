"""URL fetch and HTML cleaning service."""

import logging
import requests

logger = logging.getLogger(__name__)

# Tags whose entire content (tag + children) we discard before extracting text
_STRIP_TAGS = [
    "script", "style", "noscript", "nav", "footer", "header",
    "aside", "advertisement", "iframe", "form",
]

def fetch_url(url: str, timeout: int = 15) -> str:
    """
    Fetch a URL and return cleaned plain text suitable for Claude.

    Raises:
        ValueError: if the response is not HTML or is empty.
        requests.exceptions.RequestException: on network/HTTP errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; MitchellNET-Recipes/1.0; "
            "+https://mitchellnet.local)"
        )
    }

    logger.info("Fetching URL: %s", url)
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type:
        raise ValueError(f"Expected HTML response, got: {content_type}")

    return _clean_html(response.text)

def _clean_html(html: str) -> str:
    """Strip noise tags and return plain text, capped at 12 000 chars."""
    try:
        # Use regex-free approach: split on < and discard tag tokens
        import re

        # Remove unwanted tag blocks (tag + all content until closing tag)
        for tag in _STRIP_TAGS:
            html = re.sub(
                rf"<{tag}[\s>].*?</{tag}>",
                " ",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )

        # Strip remaining HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Cap length to avoid huge Claude payloads
        if len(text) > 12_000:
            logger.info("Truncating cleaned text from %d to 12000 chars", len(text))
            text = text[:12_000]

        return text

    except Exception as e:
        logger.error("HTML cleaning failed: %s", e, exc_info=True)
        raise ValueError(f"Failed to clean HTML: {e}") from e
