from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db
from models.meal_plan import MealPlan, MealPlanEntry, DAYS, MEAL_SLOTS
from models.recipe import Recipe

meal_plan_bp = Blueprint("meal_plan", __name__, template_folder="../templates")


def _current_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())


@meal_plan_bp.route("/meal-plan/")
def view():
    week_start_str = request.args.get("week")
    if week_start_str:
        try:
            week_start = date.fromisoformat(week_start_str)
        except ValueError:
            week_start = _current_week_start()
    else:
        week_start = _current_week_start()

    plan = MealPlan.query.filter_by(week_start=week_start).first()
    recipes = Recipe.query.order_by(Recipe.name).all()

    # Build grid: days x slots
    grid = {d: {s: None for s in MEAL_SLOTS} for d in range(7)}
    if plan:
        for entry in plan.entries:
            grid[entry.day_of_week][entry.meal_slot] = entry

    prev_week = week_start - timedelta(weeks=1)
    next_week = week_start + timedelta(weeks=1)

    return render_template(
        "meal_plan/view.html",
        plan=plan,
        week_start=week_start,
        prev_week=prev_week,
        next_week=next_week,
        days=DAYS,
        meal_slots=MEAL_SLOTS,
        grid=grid,
        recipes=recipes,
    )


@meal_plan_bp.route("/meal-plan/save", methods=["POST"])
def save():
    week_start_str = request.form.get("week_start")
    try:
        week_start = date.fromisoformat(week_start_str)
    except (ValueError, TypeError):
        return redirect(url_for("meal_plan.view"))

    plan = MealPlan.query.filter_by(week_start=week_start).first()
    if not plan:
        plan = MealPlan(week_start=week_start)
        db.session.add(plan)
        db.session.flush()

    # Clear existing entries and rebuild
    for entry in list(plan.entries):
        db.session.delete(entry)
    db.session.flush()

    for day_idx in range(7):
        for slot in MEAL_SLOTS:
            key = f"entry_{day_idx}_{slot}"
            recipe_id_str = request.form.get(key, "").strip()
            if recipe_id_str:
                try:
                    recipe_id = int(recipe_id_str)
                    db.session.add(MealPlanEntry(
                        meal_plan_id=plan.id,
                        day_of_week=day_idx,
                        meal_slot=slot,
                        recipe_id=recipe_id,
                    ))
                except (ValueError, TypeError):
                    pass

    db.session.commit()
    return redirect(url_for("meal_plan.view", week=week_start_str))
