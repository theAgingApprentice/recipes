from flask import Blueprint, render_template, request, redirect
from config.database import db
from models.recipe import Cuisine

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

@admin_bp.route("/admin/")
def index():
    cuisines = Cuisine.ordered()
    return render_template("admin/index.html", cuisines=cuisines)

@admin_bp.route("/admin/cuisines/add", methods=["POST"])
def add_cuisine():
    name = request.form.get("name", "").strip()
    if name and not Cuisine.query.filter_by(name=name).first():
        db.session.add(Cuisine(name=name))
        db.session.commit()
    return redirect("/recipes/admin/")
