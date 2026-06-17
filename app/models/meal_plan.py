from config.database import db
from datetime import datetime


class MealPlan(db.Model):
    __tablename__ = "meal_plans"

    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    entries = db.relationship(
        "MealPlanEntry",
        backref="meal_plan",
        cascade="all, delete-orphan",
        order_by="MealPlanEntry.day_of_week, MealPlanEntry.meal_slot",
    )


MEAL_SLOTS = ("breakfast", "lunch", "dinner", "snack")
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class MealPlanEntry(db.Model):
    __tablename__ = "meal_plan_entries"

    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plans.id"), nullable=False)
    day_of_week = db.Column(db.SmallInteger, nullable=False)  # 0=Mon, 6=Sun
    meal_slot = db.Column(
        db.Enum("breakfast", "lunch", "dinner", "snack"),
        nullable=False,
        default="dinner",
    )
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)

    recipe = db.relationship("Recipe")
