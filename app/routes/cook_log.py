"""Cook log routes — add, edit, and delete cook log entries."""

from datetime import date

from flask import Blueprint, redirect, render_template, request

from config.database import db
from models.recipe import CookLog, Recipe

cook_log_bp = Blueprint("cook_log", __name__)

@cook_log_bp.route("/<int:recipe_id>/cook", methods=["POST"])
def add(recipe_id):
    """Create a new cook log entry dated today and redirect to the detail page."""
    Recipe.query.get_or_404(recipe_id)
    entry = CookLog(
        recipe_id=recipe_id,
        cooked_on=date.today(),
    )
    db.session.add(entry)
    db.session.commit()
    return redirect(f"/recipes/{recipe_id}")

@cook_log_bp.route("/cook-log/<int:log_id>/edit", methods=["GET", "POST"])
def edit(log_id):
    """Edit an existing cook log entry (date, rating, notes)."""
    entry = CookLog.query.get_or_404(log_id)
    if request.method == "POST":
        entry.cooked_on = request.form.get("cooked_on") or date.today()
        rating = request.form.get("rating")
        entry.rating = int(rating) if rating else None
        entry.notes = request.form.get("notes", "").strip() or None
        db.session.commit()
        return redirect(f"/recipes/{entry.recipe_id}")
    return render_template("cook_log/edit.html", entry=entry)

@cook_log_bp.route("/cook-log/<int:log_id>/delete", methods=["POST"])
def delete(log_id):
    """Delete a cook log entry and redirect to the detail page."""
    entry = CookLog.query.get_or_404(log_id)
    recipe_id = entry.recipe_id
    db.session.delete(entry)
    db.session.commit()
    return redirect(f"/recipes/{recipe_id}")
