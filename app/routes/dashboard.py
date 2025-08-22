from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.tool import Tool
from app.models.company import Company
from app.models.blog import BlogPost
from app.models.qa import Question, Answer
from app.models.user import User
from app.models.store import Store
from app.models.product import Product, Embellishment
from app.models.product_category import ProductCategory
from app.models.subscription import CompanySubscription
from app.forms.company import CompanyForm
from app.forms.sales_setup_forms import StoresSetupForm, CategoriesSetupForm, ProductsSetupForm
from app.utils.decorators import company_required
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from app.services.analytics_service import AnalyticsService
from flask import current_app

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Main landing page"""
    stats = {
        'users': User.query.count(),
        'companies': Company.query.count(),
        'data_points': 2000000,  # This would need to be calculated from actual data tables
        'satisfaction': 99  # This is a static value for now
    }
    return render_template('index.html', stats=stats)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard page - redirects to admin dashboard if user is admin"""
    # Check if user is admin and redirect to admin dashboard
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Initialize analytics service
    analytics_service = AnalyticsService()
    
    # Get date range for analytics (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Initialize dashboard data
    dashboard_data = {}
    
    if current_user.company_id:
        # Get sales data for analytics
        df = analytics_service.get_company_sales_data(current_user.company_id, start_date, end_date)
        
        if not df.empty:
            # Get full dashboard summary for admins and users with analytics permission
            if current_user.role_company in ['admin', 'moderator']:
                dashboard_data = analytics_service.get_dashboard_summary(df)
            else:
                # Get daily summary for regular users
                today = pd.Timestamp.now().normalize()
                today_sales = df[df['sale_date'].dt.normalize() == today]
                
                dashboard_data = {
                    'today_sales': today_sales['total'].sum(),
                    'today_transactions': len(today_sales),
                    'avg_transaction': df['total'].mean() if not df.empty else 0,
                    'store_daily_goal': 1000,  # This should come from company settings
                    'store_goal_progress': (today_sales['total'].sum() / 1000 * 100) if not today_sales.empty else 0
                }
                
                # Create daily performance chart for regular users
                if not today_sales.empty:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    hourly_sales = today_sales.groupby(today_sales['sale_date'].dt.hour)['total'].sum()
                    ax.plot(hourly_sales.index, hourly_sales.values, marker='o')
                    ax.set_title('Today\'s Sales by Hour')
                    ax.set_xlabel('Hour')
                    ax.set_ylabel('Sales ($)')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    # Convert plot to base64
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    dashboard_data['daily_chart'] = base64.b64encode(buffer.getvalue()).decode()
                    plt.close()
    
    # Get stats for subscriber dashboard
    stats = {
        'questions': Question.query.filter_by(user_id=current_user.id).count(),
        'blog_count': BlogPost.query.count(),
        'users': User.query.count(),
        'companies': Company.query.count()
    }
    
    # Add company-specific stats if user has a company
    if current_user.company_id:
        stats['team_members'] = User.query.filter_by(company_id=current_user.company_id).count()
        company = Company.query.get(current_user.company_id)
        if company and company.created_at:
            days_active = (datetime.utcnow() - company.created_at).days
            stats['days_active'] = max(1, days_active)  # Ensure at least 1 day
        else:
            stats['days_active'] = 1
            
        # Get store, category, and product counts for the company
        stats['stores'] = Store.query.filter_by(company_id=current_user.company_id).count()
        stats['categories'] = ProductCategory.query.filter_by(company_id=current_user.company_id).count()
        stats['products'] = Product.query.filter_by(company_id=current_user.company_id).count()
        stats['embellishments'] = Embellishment.query.filter_by(company_id=current_user.company_id).count()
    
    # Get tools, recent blog posts, and questions
    user_tools = Tool.query.filter_by(creator_id=current_user.id).all()
    recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
    recent_questions = Question.query.order_by(Question.created_at.desc()).limit(5).all()
    
    # Get subscription information
    subscription = None
    subscription_features = {}
    if current_user.company_id:
        subscription = CompanySubscription.query.filter_by(company_id=current_user.company_id).first()
        # Default free plan features
        subscription_features = {
            'max_stores': 3,
            'max_categories': 5,
            'max_products': 20,
            'max_sales': 100,
            'advanced_analytics': False,
            'data_export': False,
            'api_access': False,
            'support_level': 'Basic'
        }
        
        # Get company data for management sections
        stores = Store.query.filter_by(company_id=current_user.company_id).all()
        categories = ProductCategory.query.filter_by(company_id=current_user.company_id).all()
        recent_products = Product.query.filter_by(company_id=current_user.company_id).order_by(Product.created_at.desc()).limit(5).all()
    else:
        stores = []
        categories = []
        recent_products = []
    
    if current_user.company_id:
        company_tools = Tool.query.filter_by(
            company_id=current_user.company_id,
            is_public=True
        ).all()
    else:
        company_tools = []
        
    return render_template(
        'dashboard/overview.html',
        stats=stats,
        dashboard=dashboard_data,
        user_tools=user_tools,
        company_tools=company_tools,
        recent_posts=recent_posts,
        recent_questions=recent_questions,
        stores=stores,
        categories=categories,
        recent_products=recent_products,
        subscription=subscription,
        subscription_features=subscription_features
    )

@dashboard_bp.route('/create-company', methods=['GET', 'POST'])
@login_required
def create_company():
    """Create a new company"""
    # Check if user is already associated with a company
    if current_user.company_id:
        flash('You are already associated with a company.', 'warning')
        return redirect(url_for('dashboard.dashboard'))
    
    # Check if user role allows company creation
    if current_user.role_website not in ['subscriber', 'admin']:
        flash('Your current role does not allow company creation. Please upgrade your account.', 'warning')
        return redirect(url_for('auth.upgrade_role'))
    
    form = CompanyForm()
    if form.validate_on_submit():
        try:
            company = Company(
                company_name=form.company_name.data,
                company_email=form.company_email.data,
                phone=form.phone.data,
                admin_id=current_user.id
            )
            db.session.add(company)
            db.session.flush()  # Get company ID
            
            # BETA MODE: Assign Premium plan by default instead of Free
            from app.models.subscription import SubscriptionPlan, CompanySubscription
            premium_plan = SubscriptionPlan.query.filter_by(name="Premium").first()
            if premium_plan:
                company.subscription_plan_id = premium_plan.id
                
                # Create subscription record
                subscription = CompanySubscription(
                    company_id=company.id,
                    plan_id=premium_plan.id,
                    status="active"
                )
                subscription.user_count = 1  # Start with the admin user
                db.session.add(subscription)
            
            # Update the user's company_id and company_role
            current_user.company_id = company.id
            current_user.role_company = 'admin'  # Creator becomes admin
            db.session.commit()
            
            flash('Company created successfully! Now you can set up stores, categories, and products to start recording sales.', 'success')
            return redirect(url_for('dashboard.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating company: {str(e)}', 'error')
        
    return render_template('dashboard/create_company.html', form=form)


@dashboard_bp.route('/upgrade-plan')
@login_required
@company_required
def upgrade_plan():
    """Redirect to pricing page with upgrade information"""
    flash('Explore our premium plans to unlock more features and higher limits!', 'info')
    return redirect(url_for('pricing.index'))

@dashboard_bp.route('/manage/stores')
@login_required
@company_required
def manage_stores_redirect():
    """Redirect to the new stores module"""
    flash('This page has been moved to a dedicated stores module', 'info')
    return redirect(url_for('stores.index'))

@dashboard_bp.route('/manage/categories')
@login_required
@company_required
def manage_categories_redirect():
    """Redirect to the new categories module"""
    flash('This page has been moved to a dedicated products module', 'info')
    return redirect(url_for('products.categories'))

@dashboard_bp.route('/manage/products')
@login_required
@company_required
def manage_products_redirect():
    """Redirect to the new products module"""
    flash('This page has been moved to a dedicated products module', 'info')
    return redirect(url_for('products.index'))

@dashboard_bp.route('/manage/category/<int:category_id>/products')
@login_required
@company_required
def manage_category_products_redirect(category_id):
    """Redirect to the new category products module"""
    flash('This page has been moved to a dedicated products module', 'info')
    return redirect(url_for('products.category_products', category_id=category_id))

@dashboard_bp.route('/overview')
@login_required
def overview():
    """Render the dashboard overview page."""
    try:
        # Get date range from query parameters or default to last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Get dashboard data from analytics service
        analytics_service = AnalyticsService()
        dashboard_data = analytics_service.get_dashboard_data(
            start_date=start_date,
            end_date=end_date,
            store_id=current_user.store.id if current_user.store else None
        )
        
        # Ensure all metrics have default values
        dashboard = {
            'total_revenue': float(dashboard_data.get('total_revenue', 0)),
            'total_transactions': int(dashboard_data.get('total_transactions', 0)),
            'avg_transaction': float(dashboard_data.get('avg_transaction', 0)),
            'top_store': dashboard_data.get('top_store', 'No stores'),
            'top_product': dashboard_data.get('top_product', 'No products'),
            'this_month_sales': float(dashboard_data.get('this_month_sales', 0)),
            'daily_change': float(dashboard_data.get('daily_change', 0)),
            'weekly_change': float(dashboard_data.get('weekly_change', 0)),
            'today_sales': float(dashboard_data.get('today_sales', 0)),
            'today_transactions': int(dashboard_data.get('today_transactions', 0)),
            'store_daily_goal': float(dashboard_data.get('store_daily_goal', 0)),
            'store_goal_progress': float(dashboard_data.get('store_goal_progress', 0))
        }
        
        return render_template(
            'dashboard/overview.html',
            dashboard=dashboard,
            datetime=datetime,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        current_app.logger.error(f"Error rendering dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard. Please try again later.', 'error')
        return redirect(url_for('main.index')) 