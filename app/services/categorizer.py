"""Claude API ingredient categorization service."""

import json
import logging

from services.extractor import call_claude

logger = logging.getLogger(__name__)

_CATEGORIES = [
    "Produce", "Meat", "Seafood", "Dairy", "Eggs",
    "Grains & Pasta", "Canned & Jarred", "Condiments & Sauces",
    "Spices & Seasonings", "Baking", "Oils & Vinegars",
    "Frozen", "Beverages", "Other",
]

_SYSTEM_PROMPT = f"""You are a grocery categorization assistant. Given a list of recipe ingredients, assign each one a category from this exact list:

{json.dumps(_CATEGORIES)}

Return ONLY a valid JSON array with no preamble, explanation, or markdown fences. Each element must be an object with:
  {{"sort_order": integer, "category": string}}

Use the sort_order values from the input exactly. Every ingredient must appear in the output. Category must be one of the values in the list above — no variations.
"""

def categorize_ingredients(ingredients: list[dict]) -> list[dict]:
    """
    Assign a grocery category to each ingredient in the list.

    Args:
        ingredients: List of dicts with at least "name" and "sort_order" keys.

    Returns:
        Same list with "category" key populated on each item.
        Falls back to "Other" for any ingredient Claude does not return.
    """
    if not ingredients:
        return ingredients

    # Build a compact list for Claude: sort_order + name only
    payload = [
        {"sort_order": ing["sort_order"], "name": ing["name"]}
        for ing in ingredients
    ]

    prompt = f"Categorize these ingredients:\n{json.dumps(payload)}"

    logger.info("Categorizing %d ingredients", len(ingredients))

    try:
        result = call_claude(prompt)
    except Exception as e:
        logger.error("Categorization failed, defaulting to Other: %s", e)
        for ing in ingredients:
            ing.setdefault("category", "Other")
        return ingredients

    # Build a lookup: sort_order -> category
    lookup = {}
    if isinstance(result, list):
        for item in result:
            try:
                lookup[int(item["sort_order"])] = item["category"]
            except (KeyError, TypeError, ValueError):
                pass

    for ing in ingredients:
        ing["category"] = lookup.get(ing["sort_order"], "Other")

    return ingredients
