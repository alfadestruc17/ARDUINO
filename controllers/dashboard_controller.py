from flask import Blueprint, render_template
from app_context import db
from services.dashboard_service import calculate_stats

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    stats = calculate_stats(db)
    return render_template("dashboard.html", **stats)