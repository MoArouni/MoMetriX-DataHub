from functools import wraps
from flask import redirect, url_for, flash, abort, request
from flask_login import current_user

def company_required(f):
    """
    Decorator for routes that require the user to be part of a company
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.company_id:
            flash('You need to create or join a company to access this feature.', 'warning')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """
    Decorator to check if the user has a specific website role.
    Roles are: 'admin', 'moderator', 'subscriber', 'viewer'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role_website != role:
                flash(f'You need {role} privileges to access this page.', 'warning')
                return redirect(url_for('dashboard.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def company_role_required(role):
    """
    Decorator to check if the user has a specific company role.
    Roles are: 'admin', 'moderator'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.company_id:
                flash('You need to be part of a company to access this feature.', 'warning')
                return redirect(url_for('dashboard.dashboard'))
            
            if current_user.role_company != role:
                flash(f'You need {role} privileges within your company to access this page.', 'warning')
                return redirect(url_for('dashboard.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator to ensure only admin users can access a route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def subscriber_required(f):
    """
    Decorator to ensure users are at least subscribers
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role_website not in ['subscriber', 'admin']:
            flash('You need to upgrade to a subscriber account to access this feature.', 'warning')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def company_admin_required(f):
    """
    Decorator to ensure user is a company admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.company_id:
            flash('You need to create or join a company to access this feature.', 'warning')
            return redirect(url_for('dashboard.dashboard'))
        
        if current_user.role_company != 'admin' and not current_user.is_admin:
            flash('You need to be a company admin to access this page.', 'warning')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function 