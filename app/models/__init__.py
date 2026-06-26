from config.database import db
from .recipe import Recipe, Ingredient, Step, CookLog
from .meal_plan import MealPlan, MealPlanEntry
from datetime import datetime


class RejectionReason(db.Model):
    __tablename__ = 'rejection_reasons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)


class AiSuggestion(db.Model):
    __tablename__ = 'ai_suggestions'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('meal_plans.id'))
    scope = db.Column(db.String(20), nullable=False)
    composition = db.Column(db.String(20), nullable=False)
    criteria = db.Column(db.Text)
    day_of_week = db.Column(db.SmallInteger)
    meal_slot = db.Column(db.String(20))
    explanation = db.Column(db.Text)
    accepted = db.Column(db.Boolean)
    rejection_reason_id = db.Column(db.Integer, db.ForeignKey('rejection_reasons.id'))
    rejection_reason_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipe = db.relationship('Recipe', backref='ai_suggestions')
    rejection_reason = db.relationship('RejectionReason')


__all__ = ["Recipe", "Ingredient", "Step", "CookLog", "MealPlan", "MealPlanEntry", "RejectionReason", "AiSuggestion"]
