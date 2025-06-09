from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.services.analytics_service import AnalyticsService
from app.utils.decorators import company_required, subscriber_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
@company_required
@subscriber_required
def index():
    """Main analytics dashboard"""
    analytics_service = AnalyticsService()
    
    # Get date range from request or default to last 30 days
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Get sales data
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/index.html', no_data=True)
    
    # Get dashboard summary
    dashboard_data = analytics_service.get_dashboard_summary(df)
    
    return render_template('analytics/index.html', 
                         dashboard=dashboard_data,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/stores')
@login_required
@company_required
@subscriber_required
def stores():
    """Store analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)  # 3 months for store analysis
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/stores.html', no_data=True)
    
    store_analytics = analytics_service.get_store_analytics(df)
    
    return render_template('analytics/stores.html', 
                         analytics=store_analytics,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/categories')
@login_required
@company_required
@subscriber_required
def categories():
    """Category analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/categories.html', no_data=True)
    
    category_analytics = analytics_service.get_category_analytics(df)
    
    return render_template('analytics/categories.html', 
                         analytics=category_analytics,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/products')
@login_required
@company_required
@subscriber_required
def products():
    """Product analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/products.html', no_data=True)
    
    product_analytics = analytics_service.get_product_analytics(df)
    
    return render_template('analytics/products.html', 
                         analytics=product_analytics,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/payments')
@login_required
@company_required
@subscriber_required
def payments():
    """Payment method analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/payments.html', no_data=True)
    
    payment_analytics = analytics_service.get_payment_analytics(df)
    
    return render_template('analytics/payments.html', 
                         analytics=payment_analytics,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/embellishments')
@login_required
@company_required
@subscriber_required
def embellishments():
    """Embellishment analytics page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/embellishments.html', no_data=True)
    
    embellishment_analytics = analytics_service.get_embellishment_analytics(df)
    
    return render_template('analytics/embellishments.html', 
                         analytics=embellishment_analytics,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/time-analysis')
@login_required
@company_required
@subscriber_required
def time_analysis():
    """Time-based analytics (days of week and months)"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=365)  # 1 year for time analysis
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/time_analysis.html', no_data=True)
    
    day_analytics = analytics_service.get_day_analytics(df)
    month_analytics = analytics_service.get_monthly_analytics(df)
    
    return render_template('analytics/time_analysis.html', 
                         day_analytics=day_analytics,
                         month_analytics=month_analytics,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/reports')
@login_required
@company_required
@subscriber_required
def reports():
    """Performance reports page"""
    analytics_service = AnalyticsService()
    
    # Get date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        flash('No sales data found for the selected period.', 'info')
        return render_template('analytics/reports.html', no_data=True)
    
    reports_data = analytics_service.generate_reports(df)
    
    return render_template('analytics/reports.html', 
                         reports=reports_data,
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/api/data')
@login_required
@company_required
@subscriber_required
def api_data():
    """API endpoint for analytics data (for AJAX requests)"""
    analytics_service = AnalyticsService()
    
    # Get parameters
    analysis_type = request.args.get('type', 'dashboard')
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
    
    if df.empty:
        return jsonify({'error': 'No data found'})
    
    # Return different data based on type
    if analysis_type == 'dashboard':
        data = analytics_service.get_dashboard_summary(df)
    elif analysis_type == 'stores':
        data = analytics_service.get_store_analytics(df)
    elif analysis_type == 'categories':
        data = analytics_service.get_category_analytics(df)
    elif analysis_type == 'products':
        data = analytics_service.get_product_analytics(df)
    elif analysis_type == 'payments':
        data = analytics_service.get_payment_analytics(df)
    elif analysis_type == 'embellishments':
        data = analytics_service.get_embellishment_analytics(df)
    elif analysis_type == 'days':
        data = analytics_service.get_day_analytics(df)
    elif analysis_type == 'months':
        data = analytics_service.get_monthly_analytics(df)
    elif analysis_type == 'reports':
        data = analytics_service.generate_reports(df)
    else:
        return jsonify({'error': 'Invalid analysis type'})
    
    return jsonify(data) 