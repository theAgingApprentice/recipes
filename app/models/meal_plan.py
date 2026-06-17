from config.database import db
from datetime import datetime


class MealPlan(db.Model):
    __tablename__ = "meal_plans"

    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    entries = db.relationship("MealPlanEntry", backref="meal_plan", cascade="all, delete-orphan")


class MealPlanEntry(db.Model):
    __tablename__ = "meal_plan_entries"

    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plans.id"), nullable=False)
    day_of_week = db.Column(db.SmallInteger, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
