"""Import routes — URL fetch and document upload via Claude API."""

import difflib
import logging

from flask import Blueprint, flash, redirect, render_template, request

from config.database import db
from models.recipe import Ingredient, Recipe, Step
from services.categorizer import categorize_ingredients
from services.extractor import extract_from_document, extract_from_text
from services.fetcher import fetch_url

logger = logging.getLogger(__name__)

import_bp = Blueprint("import_", __name__)

_ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

_DUPLICATE_THRESHOLD = 0.8

def _find_duplicate(name):
    """
    Find an existing recipe whose name closely matches the given name.

    Case-insensitive. An exact match scores 1.0 and is automatically
    included, since 1.0 >= threshold. Returns the single best-scoring
    match at or above the threshold, or None if nothing qualifies.
    """
    if not name:
        return None
    target = name.strip().lower()
    best_match = None
    best_score = 0.0
    for r in Recipe.query.all():
        score = difflib.SequenceMatcher(None, target, r.name.strip().lower()).ratio()
        if score >= _DUPLICATE_THRESHOLD and score > best_score:
            best_score = score
            best_match = r
    return best_match

# ---------------------------------------------------------------------------
# GET /import
# ---------------------------------------------------------------------------

@import_bp.route("/import")
def import_form():
    return render_template("import/import.html")

# ---------------------------------------------------------------------------
# POST /import/url
# ---------------------------------------------------------------------------

@import_bp.route("/import/url", methods=["POST"])
def import_url():
    url = request.form.get("url", "").strip()
    if not url:
        flash("Please enter a URL.", "error")
        return redirect("/recipes/import")

    try:
        text = fetch_url(url)
        recipe_data = extract_from_text(text, source_url=url)
        recipe_data["source_url"] = url
    except ValueError as e:
        flash(f"Could not extract recipe: {e}", "error")
        return redirect("/recipes/import")
    except Exception as e:
        logger.error("URL import failed: %s", e, exc_info=True)
        flash("Failed to fetch or extract the recipe. Check the URL and try again.", "error")
        return redirect("/recipes/import")

    duplicate = _find_duplicate(recipe_data.get("name"))
    return render_template("import/review.html", recipe=recipe_data, duplicate=duplicate)

# ---------------------------------------------------------------------------
# POST /import/upload
# ---------------------------------------------------------------------------

@import_bp.route("/import/upload", methods=["POST"])
def import_upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Please choose a file to upload.", "error")
        return redirect("/recipes/import")

    media_type = file.content_type or ""
    if media_type not in _ALLOWED_MIME_TYPES:
        flash(
            f"Unsupported file type '{media_type}'. "
            "Please upload a PDF, JPEG, PNG, WebP, or GIF.",
            "error",
        )
        return redirect("/recipes/import")

    try:
        file_bytes = file.read()
        recipe_data = extract_from_document(file_bytes, media_type)
    except ValueError as e:
        flash(f"Could not extract recipe: {e}", "error")
        return redirect("/recipes/import")
    except Exception as e:
        logger.error("Document import failed: %s", e, exc_info=True)
        flash("Failed to extract the recipe from the file. Please try again.", "error")
        return redirect("/recipes/import")

    duplicate = _find_duplicate(recipe_data.get("name"))
    return render_template("import/review.html", recipe=recipe_data, duplicate=duplicate)

# ---------------------------------------------------------------------------
# POST /import/save
# ---------------------------------------------------------------------------

@import_bp.route("/import/save", methods=["POST"])
def import_save():
    f = request.form

    try:
        prep = int(f["prep_time_mins"]) if f.get("prep_time_mins") else None
        cook = int(f["cook_time_mins"]) if f.get("cook_time_mins") else None
    except ValueError:
        flash("Prep and cook times must be whole numbers.", "error")
        return redirect("/recipes/import")

    recipe = Recipe(
        name=f.get("name", "").strip(),
        source_name=f.get("source_name", "").strip() or None,
        source_url=f.get("source_url", "").strip() or None,
        cuisine=f.get("cuisine", "").strip() or None,
        protein=f.get("protein", "").strip() or None,
        prep_time_mins=prep,
        cook_time_mins=cook,
        notes=f.get("notes", "").strip() or None,
        wishlist=False,
    )
    db.session.add(recipe)
    db.session.flush()  # get recipe.id before adding children

    # Ingredients — repeated fields: ingredient_name[], ingredient_qty[]
    names = f.getlist("ingredient_name[]")
    quantities = f.getlist("ingredient_qty[]")
    ingredients = []
    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            continue
        ing = Ingredient(
            recipe_id=recipe.id,
            name=name,
            quantity=quantities[i].strip() if i < len(quantities) else None,
            sort_order=i,
        )
        db.session.add(ing)
        ingredients.append({"sort_order": i, "name": name})

    # Steps — repeated field: step[]
    steps = f.getlist("step[]")
    for i, instruction in enumerate(steps, start=1):
        instruction = instruction.strip()
        if not instruction:
            continue
        db.session.add(Step(
            recipe_id=recipe.id,
            step_number=i,
            instruction=instruction,
        ))

    db.session.commit()

    # Categorize ingredients asynchronously — best-effort, non-blocking
    try:
        categorized = categorize_ingredients(ingredients)
        for item in categorized:
            ing_obj = Ingredient.query.filter_by(
                recipe_id=recipe.id, sort_order=item["sort_order"]
            ).first()
            if ing_obj:
                ing_obj.category = item["category"]
        db.session.commit()
    except Exception as e:
        logger.error("Post-save categorization failed (non-fatal): %s", e)

    return redirect(f"/recipes/{recipe.id}")
