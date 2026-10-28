from functools import wraps
from flask import session, redirect, url_for, flash, abort, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, to_object_id

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(hashed_password, password):
    if not hashed_password or not password:
        return False
    return check_password_hash(hashed_password, password)

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    return db.users.find_one({'_id': to_object_id(user_id)})

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('You are not authorized to view that page.', 'danger')
                # Redirect to appropriate dashboard based on their role
                if user_role == 'donor':
                    return redirect(url_for('donor.dashboard'))
                elif user_role == 'ngo':
                    return redirect(url_for('ngo.dashboard'))
                elif user_role == 'recipient':
                    return redirect(url_for('recipient.dashboard'))
                elif user_role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('public.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
