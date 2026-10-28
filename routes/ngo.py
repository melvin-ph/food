from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db, to_object_id
from services.auth_service import login_required, role_required, get_current_user
from services.donation_service import list_donations, get_donation_by_id
from services.request_service import get_requests_for_recipient, submit_request, cancel_request, confirm_collection

ngo_bp = Blueprint('ngo', __name__, url_prefix='/ngo')

@ngo_bp.route('/dashboard')
@login_required
@role_required('ngo')
def dashboard():
    user = get_current_user()
    db = get_db()
    
    # Summary metrics
    available_donations_count = db.donations.count_documents({'status': {'$in': ['Available', 'Partially Reserved']}})
    my_requests = get_requests_for_recipient(user['_id'])
    
    submitted_count = len(my_requests)
    approved_count = len([r for r in my_requests if r['status'] == 'Approved'])
    collected_count = len([r for r in my_requests if r['status'] in ['Collected', 'Completed']])
    
    # Calculate total food collected by this NGO
    total_food_collected = sum([r['requested_quantity'] for r in my_requests if r['status'] in ['Collected', 'Completed']])

    # Nearby / Available food donations preview
    nearby_donations, _ = list_donations(
        {'status': ['Available', 'Partially Reserved']},
        page=1,
        per_page=6
    )

    return render_template(
        'ngo/dashboard.html',
        user=user,
        available_donations_count=available_donations_count,
        submitted_count=submitted_count,
        approved_count=approved_count,
        collected_count=collected_count,
        total_food_collected=round(total_food_collected, 1),
        nearby_donations=nearby_donations,
        my_requests=my_requests[:5]
    )

@ngo_bp.route('/browse')
@login_required
@role_required('ngo')
def browse():
    user = get_current_user()
    db = get_db()
    categories = [c['name'] for c in db.categories.find().sort('name', 1)]

    category = request.args.get('category', 'All')
    food_class = request.args.get('food_classification', 'All')
    search = request.args.get('search', '')
    min_qty = request.args.get('min_qty', '')

    filters = {
        'status': ['Available', 'Partially Reserved'],
        'category': category,
        'food_classification': food_class,
        'search': search,
        'min_qty': min_qty
    }

    donations, total = list_donations(filters, page=1, per_page=30)

    return render_template(
        'ngo/browse.html',
        user=user,
        donations=donations,
        categories=categories,
        current_category=category,
        current_class=food_class,
        search=search,
        min_qty=min_qty,
        total=total
    )

@ngo_bp.route('/requests')
@login_required
@role_required('ngo')
def requests():
    user = get_current_user()
    status_filter = request.args.get('status')
    my_requests = get_requests_for_recipient(user['_id'], status=status_filter)
    return render_template('ngo/requests.html', user=user, requests=my_requests, active_status=status_filter)

@ngo_bp.route('/requests/submit', methods=['POST'])
@login_required
@role_required('ngo')
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
        return redirect(request.referrer or url_for('ngo.browse'))

    flash('Food request submitted successfully! The donor has been notified to review your collection request.', 'success')
    return redirect(url_for('ngo.requests'))

@ngo_bp.route('/requests/<request_id>/cancel', methods=['POST'])
@login_required
@role_required('ngo')
def cancel_req(request_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Cancelled by NGO')
    success, msg = cancel_request(request_id, user['_id'], reason)
    if success:
        flash(msg, 'info')
    else:
        flash(msg, 'danger')
    return redirect(url_for('ngo.requests'))

@ngo_bp.route('/requests/<request_id>/confirm-pickup', methods=['POST'])
@login_required
@role_required('ngo')
def confirm_pickup(request_id):
    user = get_current_user()
    success, msg = confirm_collection(request_id, user['_id'])
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('ngo.requests'))

@ngo_bp.route('/collections')
@login_required
@role_required('ngo')
def collections():
    user = get_current_user()
    my_requests = get_requests_for_recipient(user['_id'])
    completed_requests = [r for r in my_requests if r['status'] in ['Approved', 'Collected', 'Completed']]
    return render_template('ngo/collections.html', user=user, collections=completed_requests)
