from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from services.auth_service import login_required, get_current_user
from services.notification_service import (
    get_user_notifications, get_unread_count, mark_notification_read, mark_all_notifications_read
)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    user = get_current_user()
    notifs = get_user_notifications(user['_id'], limit=50)
    return render_template('notifications/index.html', user=user, notifications=notifs)

@notifications_bp.route('/<notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    user = get_current_user()
    mark_notification_read(notification_id, user['_id'])
    next_url = request.form.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    user = get_current_user()
    mark_all_notifications_read(user['_id'])
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/unread-count')
def unread_count():
    user = get_current_user()
    if not user:
        return jsonify({'count': 0})
    return jsonify({'count': get_unread_count(user['_id'])})
