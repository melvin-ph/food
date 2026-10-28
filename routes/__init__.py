from .auth import auth_bp
from .public import public_bp
from .donor import donor_bp
from .ngo import ngo_bp
from .recipient import recipient_bp
from .donations import donations_bp
from .notifications import notifications_bp
from .admin import admin_bp
from .reports import reports_bp

__all__ = [
    'auth_bp',
    'public_bp',
    'donor_bp',
    'ngo_bp',
    'recipient_bp',
    'donations_bp',
    'notifications_bp',
    'admin_bp',
    'reports_bp'
]
