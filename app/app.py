import os
import logging
from flask import Flask, jsonify
from config.database import db, migrate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///:memory:"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Flask-Migrate can detect them
    with app.app_context():
        import models  # noqa: F401

    from routes.recipes import recipes_bp
    from routes.meal_plan import meal_plan_bp
    from routes.shopping import shopping_bp
    from routes.import_ import import_bp
    from routes.cook_log import cook_log_bp
    from routes.admin import admin_bp
    from routes.ai_plan import bp as ai_plan_bp
    from routes.recipe_links import bp as recipe_links_bp
    app.register_blueprint(recipes_bp)
    app.register_blueprint(meal_plan_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(cook_log_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_plan_bp)
    app.register_blueprint(recipe_links_bp)

    @app.route("/api/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "healthy", "database": "connected"})
        except Exception as e:
            logger.error("Health check failed: %s", e, exc_info=True)
            return jsonify({"status": "unhealthy", "database": "disconnected"}), 500

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("Unhandled exception: %s", e, exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()
