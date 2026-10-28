from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db, to_object_id
from services.donation_service import get_donation_by_id
from services.auth_service import get_current_user

donations_bp = Blueprint('donations', __name__, url_prefix='/donations')

@donations_bp.route('/<donation_id>')
def detail(donation_id):
    donation = get_donation_by_id(donation_id)
    if not donation:
        flash('Donation listing not found.', 'danger')
        return redirect(url_for('public.index'))

    current_user = get_current_user()
    db = get_db()

    # Check if this user already requested this donation
    user_request = None
    if current_user:
        user_request = db.donation_requests.find_one({
            'donation_id': donation['_id'],
            'recipient_id': current_user['_id']
        })

    return render_template(
        'donations/detail.html',
        donation=donation,
        user=current_user,
        user_request=user_request
    )

@donations_bp.route('/<donation_id>/report', methods=['POST'])
def report(donation_id):
    donation = get_donation_by_id(donation_id)
    if not donation:
        flash('Donation listing not found.', 'danger')
        return redirect(url_for('public.index'))

    reason = request.form.get('reason', '').strip()
    details = request.form.get('details', '').strip()
    user_id = session.get('user_id')

    if not reason:
        flash('Please select a valid reason for reporting.', 'warning')
        return redirect(url_for('donations.detail', donation_id=donation_id))

    db = get_db()
    db.reported_listings.insert_one({
        'donation_id': donation['_id'],
        'donation_title': donation.get('title'),
        'donor_id': donation.get('donor_id'),
        'reporter_user_id': to_object_id(user_id) if user_id else None,
        'reason': reason,
        'details': details,
        'status': 'Pending Review',
        'created_at': datetime.now(timezone.utc)
    })

    flash('Thank you for reporting this listing. Our administration team has been alerted and will investigate the safety and accuracy of this post.', 'info')
    return redirect(url_for('donations.detail', donation_id=donation_id))
