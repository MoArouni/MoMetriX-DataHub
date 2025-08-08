from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.services.analytics_service import AnalyticsService
from app.utils.decorators import company_required
from app.utils.permission_utils import analytics_required
from app.models.sales import Sale
from app.models.store import Store
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')
analytics_service = AnalyticsService()

def get_date_range_from_request(default_days=30):
    """Helper function to get date range from request with view all support"""
    view_all = request.args.get('view_all')
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    # Set default to current month if no dates specified
    today = datetime.now().date()
    this_month_start = today.replace(day=1)
    
    if view_all:
        # View all data - get earliest and latest dates from sales
        date_range = db.session.query(
            func.min(Sale.sale_date).label('min_date'),
            func.max(Sale.sale_date).label('max_date')
        ).filter_by(company_id=current_user.company_id).first()
        
        if date_range and date_range.min_date and date_range.max_date:
            start_date = date_range.min_date
            end_date = date_range.max_date
        else:
            # Fallback to current month if no sales data
            start_date = this_month_start
            end_date = today
    else:
        if not end_date:
            end_date = today
        else:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = today
        
        if not start_date:
            # Default to start of current month
            start_date = this_month_start
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = this_month_start
    
    return start_date, end_date, bool(view_all)

@analytics_bp.route('/')
@login_required
@company_required
@analytics_required
def index():
    """Main analytics dashboard with quick stats and links"""
    analytics_service = AnalyticsService()
    
    # Get date range from request or default to current month
    start_date, end_date, view_all = get_date_range_from_request()
    
    # Get sales data for today and this month
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        return render_template('analytics/index.html', 
                             no_data=True,
                             start_date=start_date,
                             end_date=end_date,
                             view_all=view_all)
    
    # Get dashboard summary
    dashboard_data = analytics_service.get_dashboard_summary(df)
    
    return render_template('analytics/index.html', 
                         dashboard=dashboard_data,
                         start_date=start_date,
                         end_date=end_date,
                         view_all=view_all)

@analytics_bp.route('/stores')
@login_required
@company_required
@analytics_required
def stores():
    """Store analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range with view all support
    start_date, end_date, view_all = get_date_range_from_request(90)  # 3 months for store analysis
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/stores.html', 
                             no_data=True,
                             start_date=start_date,
                             end_date=end_date,
                             view_all=view_all)
    
    store_analytics = analytics_service.get_store_analytics(df)
    
    return render_template('analytics/stores.html', 
                         analytics=store_analytics,
                         start_date=start_date,
                         end_date=end_date,
                         view_all=view_all)

@analytics_bp.route('/categories')
@login_required
@company_required
@analytics_required
def categories():
    """Category analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    start_date, end_date, view_all = get_date_range_from_request(90)
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/categories.html', 
                             no_data=True,
                             start_date=start_date,
                             end_date=end_date,
                             view_all=view_all)
    
    category_analytics = analytics_service.get_category_analytics(df)
    
    return render_template('analytics/categories.html', 
                         analytics=category_analytics,
                         start_date=start_date,
                         end_date=end_date,
                         view_all=view_all)

@analytics_bp.route('/products')
@login_required
@company_required
@analytics_required
def products():
    """Product analytics page with detailed analysis"""
    analytics_service = AnalyticsService()
    
    # Get date range with view all support
    start_date, end_date, view_all = get_date_range_from_request(90)  # 3 months for product analysis
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/products.html', 
                             no_data=True,
                             start_date=start_date,
                             end_date=end_date,
                             view_all=view_all)
    
    # Get comprehensive product analytics
    product_analytics = analytics_service.get_product_analytics(df)
    
    return render_template('analytics/products.html', 
                         analytics=product_analytics,
                         start_date=start_date,
                         end_date=end_date,
                         view_all=view_all)

@analytics_bp.route('/payments')
@login_required
@company_required
@analytics_required
def payments():
    """Payment method analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    start_date, end_date, view_all = get_date_range_from_request(90)
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/payments.html', 
                             no_data=True,
                             start_date=start_date,
                             end_date=end_date,
                             view_all=view_all)
    
    payment_analytics = analytics_service.get_payment_analytics(df)
    
    return render_template('analytics/payments.html', 
                         analytics=payment_analytics,
                         start_date=start_date,
                         end_date=end_date,
                         view_all=view_all)

@analytics_bp.route('/reports')
@login_required
@company_required
@analytics_required
def reports():
    """Performance reports page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    start_date, end_date, view_all = get_date_range_from_request(90)
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/reports.html', 
                             no_data=True,
                             start_date=start_date,
                             end_date=end_date,
                             view_all=view_all)
    
    reports_data = analytics_service.generate_reports(df)
    
    return render_template('analytics/reports.html', 
                         reports=reports_data,
                         start_date=start_date,
                         end_date=end_date,
                         view_all=view_all)

@analytics_bp.route('/api/data')
@login_required
@company_required
@analytics_required
def api_data():
    """API endpoint for analytics data (for AJAX requests)"""
    analytics_service = AnalyticsService()
    
    # Get date range
    start_date, end_date, view_all = get_date_range_from_request(30)
    
    # Get specific analytics based on type parameter
    analytics_type = request.args.get('type', 'dashboard')
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        return jsonify({'error': 'No data available for the selected period'})
    
    try:
        if analytics_type == 'dashboard':
            data = analytics_service.get_dashboard_summary(df)
        elif analytics_type == 'stores':
            data = analytics_service.get_store_analytics(df)
        elif analytics_type == 'categories':
            data = analytics_service.get_category_analytics(df)
        elif analytics_type == 'products':
            data = analytics_service.get_product_analytics(df)
        elif analytics_type == 'payments':
            data = analytics_service.get_payment_analytics(df)
        elif analytics_type == 'reports':
            data = analytics_service.generate_reports(df)
        else:
            return jsonify({'error': 'Invalid analytics type'})
        
        return jsonify({
            'data': data,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'view_all': view_all
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing analytics: {str(e)}'}) 