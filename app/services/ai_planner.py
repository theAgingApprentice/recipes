import json
import os
import anthropic
from config.database import db
from models.recipe import Recipe, CookLog
from models.meal_plan import MealPlan, MealPlanEntry
from models import AiSuggestion

CRITERIA_LABELS = {
    "most_beloved":    "Most beloved (highest average cook log rating)",
    "longest_since":   "Longest since last ate",
    "varied_cuisine":  "Most varied cuisine",
    "prep_ahead":      "Prep-ahead friendly",
    "from_wishlist":   "From wishlist",
    "surprise_me":     "Surprise me",
}

def build_recipe_context(composition):
    """Return a list of recipe dicts enriched with cook log summary data."""
    recipes = Recipe.query.all()
    context = []
    for r in recipes:
        logs = CookLog.query.filter_by(recipe_id=r.id).all()
        avg_rating = (
            round(sum(l.rating for l in logs if l.rating) /
                  len([l for l in logs if l.rating]), 1)
            if any(l.rating for l in logs) else None
        )
        last_cooked = (
            max(l.cooked_on for l in logs if l.cooked_on)
            if any(l.cooked_on for l in logs) else None
        )
        # Filter by composition
        if composition == "mains_only" and r.dish_type and r.dish_type.name not in ("Main", "Other"):
            continue
        context.append({
            "id":           r.id,
            "name":         r.name,
            "cuisine":      r.cuisine.name if r.cuisine else None,
            "dish_type":    r.dish_type.name if r.dish_type else None,
            "prep_ahead":   r.prep_ahead,
            "wishlist":     r.wishlist,
            "cook_count":   len(logs),
            "avg_rating":   avg_rating,
            "last_cooked":  str(last_cooked) if last_cooked else None,
        })
    return context

def build_prompt(scope, composition, criteria, meal_plan_id=None):
    """Build the user prompt sent to Claude."""
    recipe_context = build_recipe_context(composition)
    criteria_text = "\n".join(
        f"- {CRITERIA_LABELS.get(c, c)}" for c in criteria
    )
    scope_instruction = {
        "meal":  "Suggest exactly 1 recipe for a single meal slot.",
        "day":   "Suggest recipes for breakfast, lunch, and dinner for one day.",
        "week":  "Suggest recipes for dinner slots Monday through Sunday (7 recipes).",
    }.get(scope, "Suggest 1 recipe.")

    composition_instruction = (
        "Only suggest Main or Other dish types."
        if composition == "mains_only"
        else "For dinner slots, suggest a starter, main, and dessert as a set."
    )

    return f"""You are a meal planning assistant. Select recipes from the list below.

RECIPES AVAILABLE (JSON):
{json.dumps(recipe_context, indent=2)}

PLANNING INSTRUCTIONS:
- Scope: {scope_instruction}
- Composition: {composition_instruction}
- Selection criteria (apply all that are relevant):
{criteria_text}

Respond with a JSON array only — no preamble, no markdown fences. Each element:
{{
  "recipe_id": <int>,
  "recipe_name": "<string>",
  "dish_type": "<string>",
  "day_of_week": <0-6 or null>,
  "meal_slot": "<breakfast|lunch|dinner|snack or null>",
  "explanation": "<one sentence why this recipe was chosen>"
}}"""

def get_suggestions(scope, composition, criteria):
    """Call Claude API and return parsed suggestion list."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = build_prompt(scope, composition, criteria)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if Claude adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    suggestions = json.loads(raw)
    return suggestions

def save_suggestions(suggestions, scope, composition, criteria, meal_plan_id=None):
    """Persist suggestions to ai_suggestions table and return saved objects."""
    saved = []
    criteria_json = json.dumps(criteria)
    for s in suggestions:
        row = AiSuggestion(
            recipe_id=s["recipe_id"],
            meal_plan_id=meal_plan_id,
            scope=scope,
            composition=composition,
            criteria=criteria_json,
            day_of_week=s.get("day_of_week"),
            meal_slot=s.get("meal_slot"),
            explanation=s.get("explanation"),
            accepted=None,
        )
        db.session.add(row)
        db.session.flush()
        saved.append({"suggestion": row, "meta": s})
    db.session.commit()
    return saved
