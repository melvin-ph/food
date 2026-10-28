from flask import Blueprint, jsonify
from services.auth_service import login_required
from services.reporting_service import get_chart_data, get_platform_metrics

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/api/chart-data')
def chart_data_api():
    return jsonify(get_chart_data())

@reports_bp.route('/api/metrics')
def metrics_api():
    return jsonify(get_platform_metrics())
