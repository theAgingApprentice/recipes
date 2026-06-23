from datetime import date, timedelta
from flask import Blueprint, render_template, request, Response
from models.meal_plan import MealPlan, DAYS, MEAL_SLOTS

shopping_bp = Blueprint("shopping", __name__, template_folder="../templates")


def _current_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())


def _build_list(plan):
    """Return a list of (category, ingredient_name, quantities) tuples, aggregated."""
    if not plan:
        return []

    # Collect all quantities per (category, normalised name)
    from collections import defaultdict
    buckets = defaultdict(lambda: {"category": "Other", "quantities": []})

    for entry in plan.entries:
        for ing in entry.recipe.ingredients:
            key = ing.name.strip().lower()
            bucket = buckets[key]
            bucket["category"] = ing.category or "Other"
            bucket["name"] = ing.name.strip()
            if ing.quantity and ing.quantity.strip():
                bucket["quantities"].append(ing.quantity.strip())

    items = []
    for bucket in buckets.values():
        qty_str = " + ".join(bucket["quantities"]) if bucket["quantities"] else ""
        items.append((bucket["category"], bucket["name"], qty_str))

    items.sort(key=lambda x: (x[0], x[1]))
    return items


@shopping_bp.route("/shopping-list/")
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
    items = _build_list(plan)

    return render_template(
        "shopping/view.html",
        week_start=week_start,
        plan=plan,
        items=items,
        days=DAYS,
        meal_slots=MEAL_SLOTS,
    )


@shopping_bp.route("/shopping-list/export")
def export():
    week_start_str = request.args.get("week")
    if week_start_str:
        try:
            week_start = date.fromisoformat(week_start_str)
        except ValueError:
            week_start = _current_week_start()
    else:
        week_start = _current_week_start()

    plan = MealPlan.query.filter_by(week_start=week_start).first()
    items = _build_list(plan)

    lines = [f"Shopping list — week of {week_start}\n"]
    current_cat = None
    for cat, name, qty in items:
        if cat != current_cat:
            lines.append(f"\n{cat}:")
            current_cat = cat
        lines.append(f"  {'[ ] '}{qty + ' ' if qty else ''}{name}")

    text = "\n".join(lines)
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename=shopping-{week_start}.txt"},
    )
