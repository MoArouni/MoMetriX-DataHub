from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    Decorator for routes that require admin access
    
    Usage:
        @app.route('/admin')
        @login_required
        @admin_required
        def admin():
            return 'Admin page'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('This page requires administrator access.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
    
def company_required(f):
    """
    Decorator for routes that require user to be part of a company
    
    Usage:
        @app.route('/company/dashboard')
        @login_required
        @company_required
        def company_dashboard():
            return 'Company dashboard'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.company_id:
            flash('You need to be part of a company to access this page.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function 