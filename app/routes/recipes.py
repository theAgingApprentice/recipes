from flask import Blueprint, jsonify, request
from config.database import db
from models.recipe import Recipe

recipes_bp = Blueprint("recipes", __name__)


@recipes_bp.route("/")
def index():
    return jsonify({"message": "Recipes app — use /api/recipes"})


@recipes_bp.route("/api/recipes")
def list_recipes():
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


@recipes_bp.route("/api/recipes/")
def get_recipe(recipe_id):
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
