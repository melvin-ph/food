from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import get_db, to_object_id
from services.auth_service import login_required, role_required, get_current_user
from services.reporting_service import get_platform_metrics, get_chart_data
from services.donation_service import list_donations, cancel_donation
from services.notification_service import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    user = get_current_user()
    metrics = get_platform_metrics()
    chart_data = get_chart_data()
    db = get_db()

    # Recent activities
    recent_donations = list(db.donations.find().sort('created_at', -1).limit(5))
    recent_requests = list(db.donation_requests.find().sort('created_at', -1).limit(5))
    recent_reports = list(db.reported_listings.find({'status': 'Pending Review'}).limit(5))
    recent_logs = list(db.audit_logs.find().sort('created_at', -1).limit(10))

    return render_template(
        'admin/dashboard.html',
        user=user,
        metrics=metrics,
        chart_data=chart_data,
        recent_donations=recent_donations,
        recent_requests=recent_requests,
        recent_reports=recent_reports,
        recent_logs=recent_logs
    )

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    user = get_current_user()
    role_filter = request.args.get('role')
    status_filter = request.args.get('status')
    
    db = get_db()
    query = {}
    if role_filter and role_filter != 'All':
        query['role'] = role_filter
    if status_filter and status_filter != 'All':
        query['status'] = status_filter

    all_users = list(db.users.find(query).sort('created_at', -1))
    return render_template('admin/users.html', user=user, users=all_users, active_role=role_filter, active_status=status_filter)

@admin_bp.route('/users/<user_id>/status', methods=['POST'])
@login_required
@role_required('admin')
def user_status(user_id):
    admin_user = get_current_user()
    action = request.form.get('action')  # suspend, activate, verify
    db = get_db()
    uid = to_object_id(user_id)
    if not uid:
        flash('Invalid user ID', 'danger')
        return redirect(url_for('admin.users'))

    target_user = db.users.find_one({'_id': uid})
    if not target_user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))

    now = datetime.now(timezone.utc)
    if action == 'suspend':
        db.users.update_one({'_id': uid}, {'$set': {'status': 'suspended', 'updated_at': now}})
        flash(f"Account for {target_user.get('email')} suspended.", 'warning')
    elif action == 'activate':
        db.users.update_one({'_id': uid}, {'$set': {'status': 'active', 'updated_at': now}})
        flash(f"Account for {target_user.get('email')} activated.", 'success')
    elif action == 'verify':
        db.users.update_one({'_id': uid}, {'$set': {'verified': True, 'updated_at': now}})
        create_notification(
            user_id=uid,
            title='Account Verified!',
            message='Your account has been officially verified by the FoodShare administrative team.',
            notif_type='success'
        )
        flash(f"Account for {target_user.get('email')} marked as verified.", 'success')

    db.audit_logs.insert_one({
        'action': f"USER_{action.upper()}",
        'entity_type': 'user',
        'entity_id': uid,
        'user_id': admin_user['_id'],
        'details': f"Admin {action}ed user {target_user.get('email')}",
        'created_at': now
    })

    return redirect(url_for('admin.users'))

@admin_bp.route('/donations')
@login_required
@role_required('admin')
def donations():
    user = get_current_user()
    status_filter = request.args.get('status')
    search_filter = request.args.get('search')
    
    filters = {}
    if status_filter and status_filter != 'All':
        filters['status'] = status_filter
    else:
        filters['status'] = None
    if search_filter:
        filters['search'] = search_filter

    donations_list, total = list_donations(filters, page=1, per_page=100)
    return render_template('admin/donations.html', user=user, donations=donations_list, active_status=status_filter)

@admin_bp.route('/donations/<donation_id>/cancel', methods=['POST'])
@login_required
@role_required('admin')
def cancel_donation_admin(donation_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Cancelled by administrator due to policy review')
    success, err = cancel_donation(donation_id, user['_id'], reason)
    if success:
        flash('Donation listing cancelled by admin.', 'info')
    else:
        flash(err, 'danger')
    return redirect(url_for('admin.donations'))

@admin_bp.route('/requests')
@login_required
@role_required('admin')
def requests():
    user = get_current_user()
    db = get_db()
    status_filter = request.args.get('status')
    query = {}
    if status_filter and status_filter != 'All':
        query['status'] = status_filter
    all_requests = list(db.donation_requests.find(query).sort('created_at', -1))
    return render_template('admin/requests.html', user=user, requests=all_requests, active_status=status_filter)

@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    user = get_current_user()
    metrics = get_platform_metrics()
    chart_data = get_chart_data()
    return render_template('admin/reports.html', user=user, metrics=metrics, chart_data=chart_data)

@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def categories():
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        cat_name = request.form.get('name', '').strip()
        icon = request.form.get('icon', 'bi-box-seam').strip()

        if action == 'add' and cat_name:
            if not db.categories.find_one({'name': {'$regex': f"^{cat_name}$", '$options': 'i'}}):
                db.categories.insert_one({
                    'name': cat_name,
                    'icon': icon,
                    'created_at': datetime.now(timezone.utc)
                })
                flash(f"Category '{cat_name}' added successfully.", 'success')
            else:
                flash(f"Category '{cat_name}' already exists.", 'warning')

        elif action == 'delete':
            cat_id = to_object_id(request.form.get('category_id'))
            if cat_id:
                db.categories.delete_one({'_id': cat_id})
                flash('Category removed.', 'info')

        return redirect(url_for('admin.categories'))

    categories_list = list(db.categories.find().sort('name', 1))
    return render_template('admin/categories.html', user=user, categories=categories_list)

@admin_bp.route('/reported-listings')
@login_required
@role_required('admin')
def reported_listings():
    user = get_current_user()
    db = get_db()
    reports_list = list(db.reported_listings.find().sort('created_at', -1))
    return render_template('admin/reported_listings.html', user=user, reports=reports_list)

@admin_bp.route('/audit-logs')
@login_required
@role_required('admin')
def audit_logs():
    user = get_current_user()
    db = get_db()
    logs = list(db.audit_logs.find().sort('created_at', -1).limit(100))
    return render_template('admin/audit_logs.html', user=user, logs=logs)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def settings():
    user = get_current_user()
    db = get_db()
    settings_doc = db.platform_settings.find_one({'type': 'global'}) or {}

    if request.method == 'POST':
        new_settings = {
            'type': 'global',
            'platform_name': request.form.get('platform_name', 'FoodShare'),
            'tagline': request.form.get('tagline', 'Good Food. Brighter Tomorrows.'),
            'support_email': request.form.get('support_email', 'support@foodshare.com'),
            'disclaimer': request.form.get('disclaimer', ''),
            'individual_max_units': int(request.form.get('individual_max_units', 10)),
            'updated_at': datetime.now(timezone.utc)
        }
        db.platform_settings.update_one({'type': 'global'}, {'$set': new_settings}, upsert=True)
        flash('Platform configuration settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', user=user, settings=settings_doc)
