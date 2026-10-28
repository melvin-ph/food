from flask import Blueprint, render_template, request, flash, redirect, url_for
from services.donation_service import list_donations
from services.reporting_service import get_platform_metrics
from database import get_db

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    # Fetch recent available donations for the landing page showcase
    recent_donations, _ = list_donations({'status': ['Available', 'Partially Reserved']}, page=1, per_page=6)
    metrics = get_platform_metrics()
    return render_template('index.html', donations=recent_donations, metrics=metrics)

@public_bp.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@public_bp.route('/impact')
def impact():
    metrics = get_platform_metrics()
    return render_template('impact.html', metrics=metrics)

@public_bp.route('/about')
def about():
    return render_template('about.html')

@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please complete all required fields.', 'danger')
            return render_template('contact.html')

        db = get_db()
        db.contact_messages.insert_one({
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'created_at': request.date if hasattr(request, 'date') else None
        })

        flash('Thank you for contacting FoodShare! Our team will respond to your inquiry shortly.', 'success')
        return redirect(url_for('public.contact'))

    return render_template('contact.html')

@public_bp.route('/food-safety')
def food_safety():
    return render_template('food_safety.html')
