from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from config.database import db
from models.recipe import Recipe, Ingredient, Step

recipes_bp = Blueprint("recipes", __name__, template_folder="../templates")

CUISINES = ["American", "Asian", "Italian", "Mediterranean", "Mexican", "Other"]
PROTEINS = ["Beef", "Chicken", "Fish", "Pork", "Vegan", "Vegetarian", "Other"]


@recipes_bp.route("/")
def browse():
    cuisine = request.args.get("cuisine", "")
    protein = request.args.get("protein", "")
    wishlist = request.args.get("wishlist", "")
    q = Recipe.query
    if cuisine:
        q = q.filter(Recipe.cuisine == cuisine)
    if protein:
        q = q.filter(Recipe.protein == protein)
    if wishlist == "1":
        q = q.filter(Recipe.wishlist == True)  # noqa: E712
    recipes = q.order_by(Recipe.name).all()
    return render_template(
        "recipes/browse.html",
        recipes=recipes,
        cuisines=CUISINES,
        proteins=PROTEINS,
        filters={"cuisine": cuisine, "protein": protein, "wishlist": wishlist},
    )


@recipes_bp.route("/<int:recipe_id>")
def detail(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    return render_template("recipes/detail.html", recipe=r)


@recipes_bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        r = _recipe_from_form(Recipe())
        db.session.add(r)
        db.session.flush()
        _save_ingredients(r)
        _save_steps(r)
        db.session.commit()
        return redirect(f"/recipes/{r.id}")
    return render_template("recipes/form.html", recipe=None, cuisines=CUISINES, proteins=PROTEINS)


@recipes_bp.route("/<int:recipe_id>/edit", methods=["GET", "POST"])
def edit(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if request.method == "POST":
        r = _recipe_from_form(r)
        for ing in list(r.ingredients):
            db.session.delete(ing)
        for step in list(r.steps):
            db.session.delete(step)
        db.session.flush()
        _save_ingredients(r)
        _save_steps(r)
        db.session.commit()
        return redirect(f"/recipes/{r.id}")
    return render_template("recipes/form.html", recipe=r, cuisines=CUISINES, proteins=PROTEINS)


@recipes_bp.route("/<int:recipe_id>/delete", methods=["POST"])
def delete(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for("recipes.browse"))


# --- JSON API ---

@recipes_bp.route("/api/recipes")
def api_list():
    recipes = Recipe.query.order_by(Recipe.name).all()
    return jsonify([
        {
            "id": r.id,
            "name": r.name,
            "cuisine": r.cuisine,
            "protein": r.protein,
            "prep_time_mins": r.prep_time_mins,
            "wishlist": r.wishlist,
        }
        for r in recipes
    ])


@recipes_bp.route("/api/recipes/<int:recipe_id>")
def api_detail(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    return jsonify({
        "id": r.id,
        "name": r.name,
        "source_name": r.source_name,
        "source_url": r.source_url,
        "cuisine": r.cuisine,
        "protein": r.protein,
        "prep_time_mins": r.prep_time_mins,
        "cook_time_mins": r.cook_time_mins,
        "notes": r.notes,
        "wishlist": r.wishlist,
        "ingredients": [
            {"name": i.name, "quantity": i.quantity, "category": i.category}
            for i in r.ingredients
        ],
        "steps": [
            {"step_number": s.step_number, "instruction": s.instruction}
            for s in r.steps
        ],
        "cook_logs": [
            {"cooked_on": str(c.cooked_on), "rating": c.rating, "notes": c.notes}
            for c in r.cook_logs
        ],
    })


# --- Helpers ---

def _recipe_from_form(r):
    r.name = request.form["name"].strip()
    r.source_name = request.form.get("source_name", "").strip() or None
    r.source_url = request.form.get("source_url", "").strip() or None
    r.cuisine = request.form.get("cuisine") or None
    r.protein = request.form.get("protein") or None
    r.prep_time_mins = _int_or_none(request.form.get("prep_time_mins"))
    r.cook_time_mins = _int_or_none(request.form.get("cook_time_mins"))
    r.notes = request.form.get("notes", "").strip() or None
    r.wishlist = bool(request.form.get("wishlist"))
    return r


def _save_ingredients(r):
    names = request.form.getlist("ingredient_name")
    quantities = request.form.getlist("ingredient_quantity")
    categories = request.form.getlist("ingredient_category")
    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            continue
        db.session.add(Ingredient(
            recipe_id=r.id,
            name=name,
            quantity=quantities[i].strip() if i < len(quantities) else None,
            category=categories[i].strip() if i < len(categories) else None,
            sort_order=i,
        ))


def _save_steps(r):
    instructions = request.form.getlist("step_instruction")
    for i, instruction in enumerate(instructions):
        instruction = instruction.strip()
        if not instruction:
            continue
        db.session.add(Step(
            recipe_id=r.id,
            step_number=i + 1,
            instruction=instruction,
        ))


def _int_or_none(val):
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None
