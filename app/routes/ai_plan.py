import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from config.database import db
from models.meal_plan import MealPlan, MealPlanEntry
from models.recipe import Recipe
from models import AiSuggestion, RejectionReason
from services.ai_planner import get_suggestions, save_suggestions

bp = Blueprint('ai_plan', __name__, url_prefix='/ai-plan')

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


@bp.route('/suggest', methods=['GET', 'POST'])
def suggest():
    meal_plans = MealPlan.query.order_by(MealPlan.week_start.desc()).all()
    if request.method == 'POST':
        scope = request.form.get('scope', 'meal')
        composition = request.form.get('composition', 'mains_only')
        criteria = request.form.getlist('criteria')
        meal_plan_id = request.form.get('meal_plan_id') or None
        if meal_plan_id:
            meal_plan_id = int(meal_plan_id)
        if not criteria:
            flash('Please select at least one planning criterion.', 'warning')
            return redirect(url_for('ai_plan.suggest'))
        try:
            suggestions = get_suggestions(scope, composition, criteria)
            saved = save_suggestions(suggestions, scope, composition, criteria, meal_plan_id)
            suggestion_ids = [s['suggestion'].id for s in saved]
            return redirect(url_for('ai_plan.review', ids=','.join(str(i) for i in suggestion_ids)))
        except Exception as e:
            flash(f'AI planning failed: {e}', 'danger')
            return redirect(url_for('ai_plan.suggest'))
    return render_template('ai_plan/suggest.html', meal_plans=meal_plans)


@bp.route('/review')
def review():
    ids = request.args.get('ids', '')
    if not ids:
        return redirect(url_for('ai_plan.suggest'))
    id_list = [int(i) for i in ids.split(',')]
    suggestions = AiSuggestion.query.filter(AiSuggestion.id.in_(id_list)).all()
    rejection_reasons = RejectionReason.query.all()
    return render_template('ai_plan/review.html',
                           suggestions=suggestions,
                           rejection_reasons=rejection_reasons,
                           days=DAYS,
                           ids=ids)


@bp.route('/accept/<int:suggestion_id>', methods=['POST'])
def accept(suggestion_id):
    s = AiSuggestion.query.get_or_404(suggestion_id)
    s.accepted = True
    if s.meal_plan_id:
        entry = MealPlanEntry(
            meal_plan_id=s.meal_plan_id,
            recipe_id=s.recipe_id,
            day_of_week=s.day_of_week,
            meal_slot=s.meal_slot,
        )
        db.session.add(entry)
    db.session.commit()
    ids = request.form.get('ids', '')
    flash(f'"{s.recipe.name}" added to your meal plan.', 'success')
    return redirect(url_for('ai_plan.review', ids=ids))


@bp.route('/reject/<int:suggestion_id>', methods=['POST'])
def reject(suggestion_id):
    s = AiSuggestion.query.get_or_404(suggestion_id)
    s.accepted = False
    reason_id = request.form.get('rejection_reason_id')
    reason_text = request.form.get('rejection_reason_text', '').strip()
    if reason_id:
        s.rejection_reason_id = int(reason_id)
    if reason_text:
        s.rejection_reason_text = reason_text
        existing = RejectionReason.query.filter_by(name=reason_text).first()
        if not existing:
            new_reason = RejectionReason(name=reason_text)
            db.session.add(new_reason)
            db.session.commit()
    db.session.commit()
    ids = request.form.get('ids', '')
    flash(f'"{s.recipe.name}" rejected.', 'info')
    return redirect(url_for('ai_plan.review', ids=ids))
