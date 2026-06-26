from flask import Blueprint, render_template, request, redirect
from config.database import db
from models.recipe import Cuisine, DishType
from models import RejectionReason

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

@admin_bp.route("/admin/")
def index():
    cuisines = Cuisine.ordered()
    dish_types = DishType.ordered()
    rejection_reasons = RejectionReason.query.order_by(
        db.case((RejectionReason.name == "Other", 1), else_=0),
        RejectionReason.name
    ).all()
    return render_template("admin/index.html",
                           cuisines=cuisines,
                           dish_types=dish_types,
                           rejection_reasons=rejection_reasons)

@admin_bp.route("/admin/cuisines/add", methods=["POST"])
def add_cuisine():
    name = request.form.get("name", "").strip()
    if name and not Cuisine.query.filter_by(name=name).first():
        db.session.add(Cuisine(name=name))
        db.session.commit()
    return redirect("/recipes/admin/")

@admin_bp.route("/admin/dish-types/add", methods=["POST"])
def add_dish_type():
    name = request.form.get("name", "").strip()
    if name and not DishType.query.filter_by(name=name).first():
        db.session.add(DishType(name=name))
        db.session.commit()
    return redirect("/recipes/admin/")

@admin_bp.route("/admin/rejection-reasons/add", methods=["POST"])
def add_rejection_reason():
    name = request.form.get("name", "").strip()
    if name and not RejectionReason.query.filter_by(name=name).first():
        db.session.add(RejectionReason(name=name))
        db.session.commit()
    return redirect("/recipes/admin/")
