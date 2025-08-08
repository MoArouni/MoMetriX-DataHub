from flask_login import current_user
from app.models.user_permissions import UserPermissions
from app.models.sales import Sale
from datetime import datetime, date
import functools
from flask import flash, redirect, url_for, abort
from functools import wraps

def get_user_permissions():
    """Get current user's permissions"""
    if not current_user.is_authenticated or not current_user.company_id:
        return None
    
    return UserPermissions.query.filter_by(
        user_id=current_user.id,
        company_id=current_user.company_id
    ).first()

def has_analytics_access():
    """Check if user has analytics access"""
    if not current_user.is_authenticated:
        return False
    
    # Site admins always have access
    if current_user.is_admin:
        return True
    
    # Company admins always have access
    if current_user.company_id and current_user.company:
        if current_user.company.admin_id == current_user.id:
            return True
    
    # Check role-based access
    if current_user.role_company == 'admin':
        return True
    
    # For regular moderators, check permissions
    permissions = get_user_permissions()
    return permissions and permissions.can_view_analytics

def has_store_access(store_id):
    """Check if user has access to a specific store"""
    if current_user.is_admin:
        return True
        
    permissions = get_user_permissions()
    if not permissions:
        return False
        
    return permissions.has_store_access(store_id)

def get_accessible_stores():
    """Get list of store IDs user can access"""
    if current_user.is_admin:
        from app.models.store import Store
        stores = Store.query.filter_by(company_id=current_user.company_id).all()
        return [store.id for store in stores]
    
    permissions = get_user_permissions()
    if not permissions:
        return []
    
    allowed_ids = permissions.allowed_store_ids
    if not allowed_ids:  # Empty means all stores
        from app.models.store import Store
        stores = Store.query.filter_by(company_id=current_user.company_id).all()
        return [store.id for store in stores]
    
    return allowed_ids

def can_view_all_sales():
    """Check if user can view all sales data"""
    if current_user.is_admin:
        return True
        
    permissions = get_user_permissions()
    if not permissions:
        return False
        
    return permissions.access_level == 'see_everything'

def can_view_own_sales_only():
    """Check if user can only view their own sales"""
    if current_user.is_admin:
        return False
        
    permissions = get_user_permissions()
    if not permissions:
        return True
        
    return permissions.access_level == 'daily_sales'

def filter_sales_by_permissions(sales_query):
    """Filter sales query based on user permissions"""
    if current_user.is_admin or can_view_all_sales():
        return sales_query
    
    # For daily_sales users, only show their own sales from today
    if can_view_own_sales_only():
        today = date.today()
        return sales_query.filter(
            Sale.user_id == current_user.id,
            Sale.sale_date == today
        )
    
    return sales_query.filter(False)  # No access

def analytics_required(f):
    """Decorator to require analytics permission"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.company:
            abort(403)
        if not current_user.has_permission('analytics'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def product_management_required(f):
    """Decorator to require product management permission"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.company:
            abort(403)
        if not current_user.has_permission('manage_products'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def store_access_required(store_id_param='store_id'):
    """Decorator to require access to a specific store"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Get store_id from kwargs or request
            store_id = kwargs.get(store_id_param)
            if not store_id:
                from flask import request
                store_id = request.form.get('store_id') or request.args.get('store_id')
            
            if store_id and not has_store_access(int(store_id)):
                flash('You don\'t have access to this store.', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def company_admin_required(f):
    """Decorator to require company admin access"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if user has a company and is the admin of that company
        if not current_user.company_id:
            flash('You need to be part of a company to access this page.', 'error')
            return redirect(url_for('dashboard.dashboard'))
        
        # Check if user is the company admin
        if not current_user.company or current_user.company.admin_id != current_user.id:
            flash('You need to be a company administrator to access this page.', 'error')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function 