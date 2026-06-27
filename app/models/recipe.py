from config.database import db
from datetime import datetime


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    source_name = db.Column(db.String(255))
    source_url = db.Column(db.Text)
    cuisine = db.Column(db.String(100))
    dish_type = db.Column(db.String(100))
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
    links = db.relationship("RecipeLink", foreign_keys="RecipeLink.recipe_id", cascade="all, delete-orphan")


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


class Cuisine(db.Model):
    __tablename__ = "cuisines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    @staticmethod
    def ordered():
        """Return all cuisines alphabetically, Other always last."""
        from sqlalchemy import case
        return Cuisine.query.order_by(
            case({"Other": 1}, value=Cuisine.name, else_=0),
            Cuisine.name
        ).all()


class RecipeLink(db.Model):
    __tablename__ = "recipe_links"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    linked_recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    linked_recipe = db.relationship("Recipe", foreign_keys=[linked_recipe_id])


class DishType(db.Model):
    __tablename__ = "dish_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    @staticmethod
    def ordered():
        """Return all dish types alphabetically, Other always last."""
        from sqlalchemy import case
        return DishType.query.order_by(
            case({"Other": 1}, value=DishType.name, else_=0),
            DishType.name
        ).all()
