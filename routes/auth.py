from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db, to_object_id
from services.auth_service import hash_password, verify_password, login_required, get_current_user
from services.notification_service import create_notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and 'user_id' in session:
        role = session.get('role')
        if role == 'donor':
            return redirect(url_for('donor.dashboard'))
        elif role == 'ngo':
            return redirect(url_for('ngo.dashboard'))
        elif role == 'recipient':
            return redirect(url_for('recipient.dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        db = get_db()
        user = db.users.find_one({'email': email})

        if not user or not verify_password(user.get('password_hash'), password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if user.get('status') == 'suspended':
            flash('This account has been suspended by an administrator. Please contact support.', 'danger')
            return render_template('auth/login.html', email=email)

        # Login successful
        session.clear()
        session['user_id'] = str(user['_id'])
        session['email'] = user['email']
        session['name'] = user.get('org_name') or user.get('name') or user.get('contact_name') or 'User'
        session['role'] = user['role']
        if remember:
            session.permanent = True

        flash(f"Welcome back, {session['name']}!", 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user['role'] == 'donor':
            return redirect(url_for('donor.dashboard'))
        elif user['role'] == 'ngo':
            return redirect(url_for('ngo.dashboard'))
        elif user['role'] == 'recipient':
            return redirect(url_for('recipient.dashboard'))
        elif user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('public.index'))

    default_role = request.args.get('role', 'donor')
    return render_template('auth/login.html', active_tab=default_role)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        role = request.form.get('role', '').strip().lower()
        if role not in ['donor', 'ngo', 'recipient']:
            flash('Invalid role selected. Administrator accounts cannot be created publicly.', 'danger')
            return redirect(url_for('auth.register'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        terms = request.form.get('terms')

        if not terms:
            flash('You must agree to the Terms of Service and Food Safety Guidelines.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if not email or '@' not in email:
            flash('Please provide a valid email address.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        db = get_db()
        if db.users.find_one({'email': email}):
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        now = datetime.now(timezone.utc)
        user_doc = {
            'email': email,
            'password_hash': hash_password(password),
            'role': role,
            'phone': phone,
            'address': address,
            'status': 'active',  # or 'pending_verification' for NGOs
            'created_at': now,
            'updated_at': now
        }

        if role == 'donor':
            user_doc['org_name'] = request.form.get('org_name', '').strip()
            user_doc['contact_name'] = request.form.get('contact_name', '').strip()
            user_doc['donor_type'] = request.form.get('donor_type', 'Restaurant')  # Restaurant, Hotel, Hostel, Caterer, Event Organizer, Other
            user_doc['verified'] = True
        elif role == 'ngo':
            user_doc['org_name'] = request.form.get('org_name', '').strip()
            user_doc['contact_name'] = request.form.get('contact_name', '').strip()
            user_doc['service_area'] = request.form.get('service_area', '').strip()
            user_doc['description'] = request.form.get('description', '').strip()
            user_doc['reg_number'] = request.form.get('reg_number', '').strip()
            user_doc['verified'] = True  # Verified by default for academic project demo
        elif role == 'recipient':
            user_doc['name'] = request.form.get('name', '').strip()
            user_doc['service_area'] = request.form.get('service_area', '').strip()
            user_doc['verified'] = True

        result = db.users.insert_one(user_doc)

        # Welcome notification
        create_notification(
            user_id=result.inserted_id,
            title='Welcome to FoodShare!',
            message='Thank you for joining our mission to reduce food waste and feed communities.',
            link='/',
            notif_type='success'
        )

        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('auth.login', role=role))

    role_param = request.args.get('role', 'donor')
    return render_template('auth/register.html', selected_role=role_param)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            update_data = {
                'phone': request.form.get('phone', '').strip(),
                'address': request.form.get('address', '').strip(),
                'updated_at': datetime.now(timezone.utc)
            }
            if user.get('role') in ['donor', 'ngo']:
                update_data['org_name'] = request.form.get('org_name', '').strip()
                update_data['contact_name'] = request.form.get('contact_name', '').strip()
            else:
                update_data['name'] = request.form.get('name', '').strip()

            db.users.update_one({'_id': user['_id']}, {'$set': update_data})
            session['name'] = update_data.get('org_name') or update_data.get('name') or session['name']
            flash('Profile details updated successfully.', 'success')
            return redirect(url_for('auth.profile'))

        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not verify_password(user.get('password_hash'), old_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))

            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return redirect(url_for('auth.profile'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('auth.profile'))

            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'password_hash': hash_password(new_password), 'updated_at': datetime.now(timezone.utc)}}
            )
            flash('Password changed successfully.', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=user)
