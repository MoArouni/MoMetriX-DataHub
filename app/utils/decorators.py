from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def company_required(f):
    """
    Decorator for routes that require the user to be part of a company
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.company_id and not current_user.is_admin:
            flash('You need to join or create a company first.', 'warning')
            return redirect(url_for('dashboard.create_company'))
            
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
                return redirect(url_for('dashboard.index'))
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
                return redirect(url_for('dashboard.index'))
            
            if current_user.role_company != role:
                flash(f'You need {role} privileges within your company to access this page.', 'warning')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator for routes that require admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def subscriber_required(f):
    """
    Decorator for routes that require subscriber role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        if current_user.role_website not in ['subscriber', 'admin']:
            flash('This feature requires a Subscriber account.', 'warning')
            return redirect(url_for('auth.upgrade_role'))
            
        return f(*args, **kwargs)
    return decorated_function

def company_admin_required(f):
    """
    Decorator for routes that require the user to be a company admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        if not current_user.company_id:
            flash('You need to join or create a company first.', 'warning')
            return redirect(url_for('dashboard.create_company'))
            
        if current_user.role_company != 'admin' and not current_user.is_admin:
            flash('You need company admin rights to access this page.', 'error')
            return redirect(url_for('dashboard.index'))
            
        return f(*args, **kwargs)
    return decorated_function 