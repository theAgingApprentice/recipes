from flask import Blueprint, request, jsonify, abort
from config.database import db
from models.recipe import Recipe, RecipeLink

bp = Blueprint("recipe_links", __name__)


@bp.route("/recipe-links/<int:recipe_id>", methods=["GET"])
def list_links(recipe_id):
    Recipe.query.get_or_404(recipe_id)
    links = RecipeLink.query.filter_by(recipe_id=recipe_id).all()
    return jsonify([
        {"link_id": lk.id, "id": lk.linked_recipe.id, "name": lk.linked_recipe.name}
        for lk in links
    ])


@bp.route("/recipe-links/", methods=["POST"])
def add_link():
    data = request.get_json(force=True)
    recipe_id = data.get("recipe_id")
    linked_recipe_id = data.get("linked_recipe_id")
    if not recipe_id or not linked_recipe_id:
        abort(400)
    if recipe_id == linked_recipe_id:
        abort(400)
    Recipe.query.get_or_404(recipe_id)
    Recipe.query.get_or_404(linked_recipe_id)
    for a, b in [(recipe_id, linked_recipe_id), (linked_recipe_id, recipe_id)]:
        if not RecipeLink.query.filter_by(recipe_id=a, linked_recipe_id=b).first():
            db.session.add(RecipeLink(recipe_id=a, linked_recipe_id=b))
    db.session.commit()
    return jsonify({"status": "ok"}), 201


@bp.route("/recipe-links/<int:link_id>/delete", methods=["POST"])
def delete_link(link_id):
    lk = RecipeLink.query.get_or_404(link_id)
    reverse = RecipeLink.query.filter_by(
        recipe_id=lk.linked_recipe_id, linked_recipe_id=lk.recipe_id
    ).first()
    db.session.delete(lk)
    if reverse:
        db.session.delete(reverse)
    db.session.commit()
    return jsonify({"status": "ok"}), 200
