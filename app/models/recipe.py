from config.database import db
from datetime import datetime


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    source_name = db.Column(db.String(255))
    source_url = db.Column(db.Text)
    cuisine = db.Column(db.String(100))
    protein = db.Column(db.String(100))
    prep_time_mins = db.Column(db.Integer)
    cook_time_mins = db.Column(db.Integer)
    notes = db.Column(db.Text)
    wishlist = db.Column(db.Boolean, nullable=False, default=False)
    prep_ahead = db.Column(db.Boolean, nullable=False, default=False)
    prep_ahead_override = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    ingredients = db.relationship("Ingredient", backref="recipe", cascade="all, delete-orphan", order_by="Ingredient.sort_order")
    steps = db.relationship("Step", backref="recipe", cascade="all, delete-orphan", order_by="Step.step_number")
    cook_logs = db.relationship("CookLog", backref="recipe", cascade="all, delete-orphan", order_by="CookLog.cooked_on.desc()")


class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.String(100))
    category = db.Column(db.String(100))
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class Step(db.Model):
    __tablename__ = "steps"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    instruction = db.Column(db.Text, nullable=False)


class CookLog(db.Model):
    __tablename__ = "cook_logs"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    cooked_on = db.Column(db.Date, nullable=False)
    rating = db.Column(db.SmallInteger)
    notes = db.Column(db.Text)
