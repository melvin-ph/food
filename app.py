import os
from datetime import datetime, timezone
from flask import Flask, render_template, session, request
from flask_wtf.csrf import CSRFProtect
from config import Config
from database import get_db, to_object_id
from services.notification_service import get_unread_count
from routes import (
    auth_bp, public_bp, donor_bp, ngo_bp, recipient_bp,
    donations_bp, notifications_bp, admin_bp, reports_bp
)

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize CSRF
    csrf.init_app(app)

    # Jinja globals
    app.jinja_env.globals['str'] = str
    app.jinja_env.globals['min'] = min
    app.jinja_env.globals['max'] = max

    # Initialize database
    get_db()

    # Register Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(recipient_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)

    # Custom Jinja Template Filters
    @app.template_filter('format_datetime')
    def format_datetime(value, format="%d %b %Y, %I:%M %p"):
        if not value:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except Exception:
                return value
        return value.strftime(format)

    @app.template_filter('format_date')
    def format_date(value, format="%d %b %Y"):
        if not value:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except Exception:
                return value
        return value.strftime(format)

    @app.template_filter('status_badge')
    def status_badge(status):
        badges = {
            'Available': 'badge-success',
            'Partially Reserved': 'badge-warning',
            'Fully Reserved': 'badge-info',
            'Collected': 'badge-success',
            'Completed': 'badge-primary',
            'Pending': 'badge-warning',
            'Approved': 'badge-info',
            'Rejected': 'badge-danger',
            'Cancelled': 'badge-danger',
            'Expired': 'badge-secondary',
            'active': 'badge-success',
            'suspended': 'badge-danger'
        }
        return badges.get(status, 'badge-secondary')

    # Context Processors for global template variables
    @app.context_processor
    def inject_global_data():
        current_user = None
        unread_notifications = 0
        if 'user_id' in session:
            db = get_db()
            current_user = db.users.find_one({'_id': to_object_id(session['user_id'])})
            if current_user:
                unread_notifications = get_unread_count(current_user['_id'])

        return {
            'current_user': current_user,
            'unread_notifications_count': unread_notifications,
            'current_year': datetime.now().year,
            'platform_brand': 'FoodShare',
            'platform_tagline': 'Good Food. Brighter Tomorrows.'
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
