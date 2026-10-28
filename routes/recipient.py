from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db, to_object_id
from services.auth_service import login_required, role_required, get_current_user
from services.donation_service import list_donations, get_donation_by_id
from services.request_service import get_requests_for_recipient, submit_request, cancel_request, confirm_collection

recipient_bp = Blueprint('recipient', __name__, url_prefix='/recipient')

@recipient_bp.route('/dashboard')
@login_required
@role_required('recipient')
def dashboard():
    user = get_current_user()
    db = get_db()

    my_requests = get_requests_for_recipient(user['_id'])
    pending_count = len([r for r in my_requests if r['status'] == 'Pending'])
    approved_count = len([r for r in my_requests if r['status'] == 'Approved'])
    collected_count = len([r for r in my_requests if r['status'] in ['Collected', 'Completed']])

    # Recommended fresh food donations available now
    donations, _ = list_donations({'status': ['Available', 'Partially Reserved']}, page=1, per_page=6)

    return render_template(
        'recipient/dashboard.html',
        user=user,
        my_requests=my_requests[:5],
        pending_count=pending_count,
        approved_count=approved_count,
        collected_count=collected_count,
        donations=donations
    )

@recipient_bp.route('/browse')
@login_required
@role_required('recipient')
def browse():
    user = get_current_user()
    db = get_db()
    categories = [c['name'] for c in db.categories.find().sort('name', 1)]

    category = request.args.get('category', 'All')
    food_class = request.args.get('food_classification', 'All')
    search = request.args.get('search', '')

    filters = {
        'status': ['Available', 'Partially Reserved'],
        'category': category,
        'food_classification': food_class,
        'search': search
    }

    donations, total = list_donations(filters, page=1, per_page=20)

    return render_template(
        'recipient/browse.html',
        user=user,
        donations=donations,
        categories=categories,
        current_category=category,
        current_class=food_class,
        search=search,
        total=total
    )

@recipient_bp.route('/my-requests')
@login_required
@role_required('recipient')
def my_requests():
    user = get_current_user()
    status_filter = request.args.get('status')
    requests_list = get_requests_for_recipient(user['_id'], status=status_filter)
    return render_template('recipient/my_requests.html', user=user, requests=requests_list, active_status=status_filter)

@recipient_bp.route('/requests/submit', methods=['POST'])
@login_required
@role_required('recipient')
def submit():
    user = get_current_user()
    data = {
        'donation_id': request.form.get('donation_id'),
        'requested_quantity': request.form.get('requested_quantity'),
        'intended_pickup_time': request.form.get('intended_pickup_time'),
        'notes': request.form.get('notes', '')
    }

    req_id, err = submit_request(user['_id'], data)
    if err:
        flash(err, 'danger')
        return redirect(request.referrer or url_for('recipient.browse'))

    flash('Food request submitted successfully! You will be notified once the donor reviews your request.', 'success')
    return redirect(url_for('recipient.my_requests'))

@recipient_bp.route('/requests/<request_id>/cancel', methods=['POST'])
@login_required
@role_required('recipient')
def cancel_req(request_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Cancelled by recipient')
    success, msg = cancel_request(request_id, user['_id'], reason)
    if success:
        flash(msg, 'info')
    else:
        flash(msg, 'danger')
    return redirect(url_for('recipient.my_requests'))

@recipient_bp.route('/requests/<request_id>/confirm-pickup', methods=['POST'])
@login_required
@role_required('recipient')
def confirm_pickup(request_id):
    user = get_current_user()
    success, msg = confirm_collection(request_id, user['_id'])
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('recipient.my_requests'))
