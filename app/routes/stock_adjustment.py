from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models.stock_adjustment import StockAdjustmentEntry
from app.models.product import Product
from app.models.store import Store
from app.models.product_category import ProductCategory
from app.utils.decorators import company_required
from app import db
from datetime import datetime

# Create stock adjustment blueprint
stock_adjustment_bp = Blueprint('stock_adjustment', __name__, url_prefix='/admin/stock-adjustment')

def company_admin_required(f):
    """Decorator to require company admin access - local version to avoid circular imports"""
    import functools
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

@stock_adjustment_bp.route('/')
@login_required
@company_required
@company_admin_required
def index():
    """Admin-only stock adjustment checklist page"""
    company_id = current_user.company_id
    
    # Get filter parameters
    status_filter = request.args.get('status', 'pending')  # pending, completed, all
    store_filter = request.args.get('store', 'all')
    category_filter = request.args.get('category', 'all')
    
    # Base query for company's stock adjustments
    query = StockAdjustmentEntry.query.filter_by(company_id=company_id)
    
    # Apply status filter
    if status_filter == 'pending':
        query = query.filter_by(is_completed=False)
    elif status_filter == 'completed':
        query = query.filter_by(is_completed=True)
    
    # Apply store filter
    if store_filter != 'all':
        query = query.filter_by(store_name=store_filter)
    
    # Apply category filter
    if category_filter != 'all':
        query = query.filter_by(category_name=category_filter)
    
    # Order by most recent first
    adjustments = query.order_by(StockAdjustmentEntry.created_at.desc()).all()
    
    # Get filter options
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
    # Calculate statistics
    total_pending = StockAdjustmentEntry.query.filter_by(
        company_id=company_id, is_completed=False
    ).count()
    
    total_completed = StockAdjustmentEntry.query.filter_by(
        company_id=company_id, is_completed=True
    ).count()
    
    stats = {
        'pending': total_pending,
        'completed': total_completed,
        'total': total_pending + total_completed
    }
    
    return render_template('stock_adjustment/index.html',
                         adjustments=adjustments,
                         stores=stores,
                         categories=categories,
                         stats=stats,
                         current_status=status_filter,
                         current_store=store_filter,
                         current_category=category_filter)

@stock_adjustment_bp.route('/complete/<int:adjustment_id>', methods=['POST'])
@login_required
@company_required
@company_admin_required
def complete_adjustment(adjustment_id):
    """Mark a stock adjustment as completed"""
    company_id = current_user.company_id
    
    adjustment = StockAdjustmentEntry.query.filter_by(
        id=adjustment_id, company_id=company_id
    ).first_or_404()
    
    if adjustment.is_completed:
        flash('This adjustment has already been completed.', 'info')
        return redirect(url_for('stock_adjustment.index'))
    
    # Get admin notes from form
    admin_notes = request.form.get('admin_notes', '').strip()
    
    # Mark as completed
    adjustment.is_completed = True
    adjustment.completed_at = datetime.utcnow()
    adjustment.completed_by = current_user.id
    adjustment.admin_notes = admin_notes if admin_notes else None
    
    db.session.commit()
    
    flash(f'Stock adjustment for {adjustment.product_name} marked as completed!', 'success')
    return redirect(url_for('stock_adjustment.index'))

@stock_adjustment_bp.route('/uncomplete/<int:adjustment_id>', methods=['POST'])
@login_required
@company_required
@company_admin_required
def uncomplete_adjustment(adjustment_id):
    """Mark a completed stock adjustment as pending again"""
    company_id = current_user.company_id
    
    adjustment = StockAdjustmentEntry.query.filter_by(
        id=adjustment_id, company_id=company_id
    ).first_or_404()
    
    if not adjustment.is_completed:
        flash('This adjustment is already pending.', 'info')
        return redirect(url_for('stock_adjustment.index'))
    
    # Mark as pending
    adjustment.is_completed = False
    adjustment.completed_at = None
    adjustment.completed_by = None
    adjustment.admin_notes = None
    
    db.session.commit()
    
    flash(f'Stock adjustment for {adjustment.product_name} marked as pending!', 'info')
    return redirect(url_for('stock_adjustment.index'))

@stock_adjustment_bp.route('/bulk-complete', methods=['POST'])
@login_required
@company_required
@company_admin_required
def bulk_complete():
    """Mark multiple adjustments as completed"""
    company_id = current_user.company_id
    
    adjustment_ids = request.form.getlist('adjustment_ids')
    if not adjustment_ids:
        flash('No adjustments selected.', 'error')
        return redirect(url_for('stock_adjustment.index'))
    
    completed_count = 0
    for adj_id in adjustment_ids:
        try:
            adjustment = StockAdjustmentEntry.query.filter_by(
                id=int(adj_id), company_id=company_id, is_completed=False
            ).first()
            
            if adjustment:
                adjustment.is_completed = True
                adjustment.completed_at = datetime.utcnow()
                adjustment.completed_by = current_user.id
                completed_count += 1
                
        except (ValueError, TypeError):
            continue
    
    db.session.commit()
    
    flash(f'Marked {completed_count} stock adjustments as completed!', 'success')
    return redirect(url_for('stock_adjustment.index'))

@stock_adjustment_bp.route('/api/stats')
@login_required
@company_required
@company_admin_required
def api_stats():
    """API endpoint for real-time stock adjustment statistics"""
    company_id = current_user.company_id
    
    total_pending = StockAdjustmentEntry.query.filter_by(
        company_id=company_id, is_completed=False
    ).count()
    
    total_completed_today = StockAdjustmentEntry.query.filter_by(
        company_id=company_id, is_completed=True
    ).filter(
        StockAdjustmentEntry.completed_at >= datetime.now().date()
    ).count()
    
    return jsonify({
        'pending': total_pending,
        'completed_today': total_completed_today
    }) 