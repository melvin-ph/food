import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database import get_db, to_object_id
from services.auth_service import login_required, role_required, get_current_user
from services.donation_service import (
    create_donation, get_donation_by_id, update_donation, cancel_donation, 
    list_donations, get_donor_stats
)
from services.request_service import (
    get_requests_for_donor, review_request, confirm_collection
)

donor_bp = Blueprint('donor', __name__, url_prefix='/donor')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@donor_bp.route('/dashboard')
@login_required
@role_required('donor')
def dashboard():
    user = get_current_user()
    stats = get_donor_stats(user['_id'])
    
    # Recent donations
    donations, _ = list_donations({'donor_id': user['_id'], 'status': None}, page=1, per_page=5)
    
    # Pending requests
    pending_requests = get_requests_for_donor(user['_id'], status='Pending')[:5]

    return render_template(
        'donor/dashboard.html',
        user=user,
        stats=stats,
        donations=donations,
        pending_requests=pending_requests
    )

@donor_bp.route('/donations')
@login_required
@role_required('donor')
def donations():
    user = get_current_user()
    status_filter = request.args.get('status')
    search_filter = request.args.get('search')
    
    filters = {'donor_id': user['_id']}
    if status_filter and status_filter != 'All':
        filters['status'] = status_filter
    else:
        filters['status'] = None  # Show all statuses for donor's own listings

    if search_filter:
        filters['search'] = search_filter

    donations_list, total = list_donations(filters, page=1, per_page=50)
    return render_template('donor/donations.html', donations=donations_list, user=user, active_status=status_filter)

@donor_bp.route('/donations/create', methods=['GET', 'POST'])
@login_required
@role_required('donor')
def create():
    user = get_current_user()
    db = get_db()
    categories = [c['name'] for c in db.categories.find().sort('name', 1)]
    if not categories:
        categories = ['Prepared Meals', 'Fresh Produce', 'Bakery & Bread', 'Dairy Products', 'Packaged Foods', 'Beverages']

    if request.method == 'POST':
        # File upload handling
        image_path = '/static/images/prepared-meals.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"donation_{user['_id']}_{file.filename}")
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                image_path = f"/static/images/uploads/{filename}"

        form_data = {
            'title': request.form.get('title'),
            'category': request.form.get('category'),
            'description': request.form.get('description'),
            'quantity': request.form.get('quantity'),
            'unit': request.form.get('unit', 'kg'),
            'food_classification': request.form.get('food_classification', 'Vegetarian'),
            'allergens': request.form.get('allergens', 'None specified'),
            'storage_instructions': request.form.get('storage_instructions', 'Keep in dry/cool place'),
            'packaging_details': request.form.get('packaging_details', 'Food grade containers'),
            'preparation_time': request.form.get('preparation_time'),
            'available_until': request.form.get('available_until'),
            'pickup_start': request.form.get('pickup_start', '10:00 AM'),
            'pickup_end': request.form.get('pickup_end', '06:00 PM'),
            'pickup_address': request.form.get('pickup_address', user.get('address')),
            'contact_instructions': request.form.get('contact_instructions'),
            'accuracy_confirmed': bool(request.form.get('accuracy_confirmed')),
            'image_path': image_path,
            'status': 'Available'
        }

        if not form_data['accuracy_confirmed']:
            flash('You must confirm that the food details and safety standards provided are accurate.', 'danger')
            return render_template('donor/create_donation.html', categories=categories, form_data=form_data, user=user)

        donation_id, error = create_donation(user['_id'], form_data)
        if error:
            flash(error, 'danger')
            return render_template('donor/create_donation.html', categories=categories, form_data=form_data, user=user)

        flash('Food donation published successfully! Nearby recipients and NGOs can now view and request it.', 'success')
        return redirect(url_for('donor.dashboard'))

    return render_template('donor/create_donation.html', categories=categories, user=user)

@donor_bp.route('/donations/<donation_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('donor')
def edit(donation_id):
    user = get_current_user()
    donation = get_donation_by_id(donation_id)
    if not donation or donation['donor_id'] != user['_id']:
        flash('Donation not found or access denied.', 'danger')
        return redirect(url_for('donor.donations'))

    db = get_db()
    categories = [c['name'] for c in db.categories.find().sort('name', 1)]
    if not categories:
        categories = ['Prepared Meals', 'Fresh Produce', 'Bakery & Bread', 'Dairy Products', 'Packaged Foods']

    if request.method == 'POST':
        update_data = {
            'title': request.form.get('title'),
            'category': request.form.get('category'),
            'description': request.form.get('description'),
            'food_classification': request.form.get('food_classification'),
            'allergens': request.form.get('allergens'),
            'storage_instructions': request.form.get('storage_instructions'),
            'packaging_details': request.form.get('packaging_details'),
            'pickup_start': request.form.get('pickup_start'),
            'pickup_end': request.form.get('pickup_end'),
            'pickup_address': request.form.get('pickup_address'),
            'contact_instructions': request.form.get('contact_instructions'),
            'available_until': request.form.get('available_until')
        }
        
        # Check if new image uploaded
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"donation_{user['_id']}_{file.filename}")
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                update_data['image_path'] = f"/static/images/uploads/{filename}"

        success, err = update_donation(donation_id, user['_id'], update_data)
        if not success:
            flash(err, 'danger')
            return render_template('donor/edit_donation.html', donation=donation, categories=categories, user=user)

        flash('Donation details updated successfully.', 'success')
        return redirect(url_for('donor.donations'))

    return render_template('donor/edit_donation.html', donation=donation, categories=categories, user=user)

@donor_bp.route('/donations/<donation_id>/cancel', methods=['POST'])
@login_required
@role_required('donor')
def cancel(donation_id):
    user = get_current_user()
    reason = request.form.get('reason', 'Cancelled by donor')
    success, err = cancel_donation(donation_id, user['_id'], reason)
    if success:
        flash('Donation listing cancelled.', 'info')
    else:
        flash(err, 'danger')
    return redirect(url_for('donor.donations'))

@donor_bp.route('/requests')
@login_required
@role_required('donor')
def requests():
    user = get_current_user()
    status_filter = request.args.get('status')
    all_requests = get_requests_for_donor(user['_id'], status=status_filter)
    return render_template('donor/requests.html', requests=all_requests, user=user, active_status=status_filter)

@donor_bp.route('/requests/<request_id>/review', methods=['POST'])
@login_required
@role_required('donor')
def review_req(request_id):
    user = get_current_user()
    action = request.form.get('action')  # approve or reject
    notes = request.form.get('notes', '')

    success, msg = review_request(request_id, user['_id'], action, notes)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('donor.requests'))

@donor_bp.route('/requests/<request_id>/collect', methods=['POST'])
@login_required
@role_required('donor')
def collect_req(request_id):
    user = get_current_user()
    success, msg = confirm_collection(request_id, user['_id'])
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('donor.requests'))

@donor_bp.route('/reports')
@login_required
@role_required('donor')
def reports():
    user = get_current_user()
    stats = get_donor_stats(user['_id'])
    all_requests = get_requests_for_donor(user['_id'], status='Collected')
    return render_template('donor/reports.html', user=user, stats=stats, completed_requests=all_requests)
