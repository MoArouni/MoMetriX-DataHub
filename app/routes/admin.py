from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, current_user, login_required
from sqlalchemy import func, desc
from app.models.user import User
from app.models.company import Company
from app.forms.auth_forms import LoginForm
from app.utils.decorators import admin_required
from app import db
from datetime import datetime, timedelta
from app.config import Config
from app.models.sales import Sale
from app.models.product import Product
from app.models.subscription import CompanySubscription

# Create admin blueprint with a complex URL prefix to hide it
admin_bp = Blueprint('admin', __name__, url_prefix='/adminr0ute$S19ou4w91048')

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Secret admin login route"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user is not None and user.verify_password(form.password.data):
            if user.is_admin:
                login_user(user, form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Logged in as administrator.', 'success')
                next_page = request.args.get('next')
                if next_page is None or not next_page.startswith('/'):
                    next_page = url_for('admin.dashboard')
                return redirect(next_page)
            else:
                flash('This account does not have administrator privileges.', 'error')
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('admin/login.html', form=form)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Website admin dashboard with website analytics"""
    
    # Get date range for filtering (default to last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # User Statistics by Role
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    subscriber_users = User.query.filter_by(role_website='subscriber').count()
    viewer_users = User.query.filter_by(role_website='viewer').count()
    new_users_30d = User.query.filter(User.created_at >= start_date).count()
    active_users_30d = User.query.filter(User.last_login >= start_date).count() if hasattr(User, 'last_login') else 0
    
    # Company Statistics
    total_companies = Company.query.count()
    new_companies_30d = Company.query.filter(Company.created_at >= start_date).count()
    active_companies = total_companies  # All companies are considered active
    
    # Newsletter Statistics
    try:
        from app.models.newsletter import NewsletterSubscriber, NewsletterCampaign
        total_subscribers = NewsletterSubscriber.query.filter_by(is_active=True).count()
        new_subscribers_30d = NewsletterSubscriber.query.filter(
            NewsletterSubscriber.subscribed_at >= start_date
        ).count()
        recent_campaigns = NewsletterCampaign.query.order_by(desc(NewsletterCampaign.created_at)).limit(3).all()
        total_campaigns = NewsletterCampaign.query.count()
    except ImportError:
        total_subscribers = 0
        new_subscribers_30d = 0
        recent_campaigns = []
        total_campaigns = 0
    
    # Content Statistics (placeholder for future blog/Q&A features)
    total_blogs = 0  # TODO: Add when blog model is created
    pending_questions = 0  # TODO: Add when Q&A model is created
    recent_blogs = []  # TODO: Add when blog model is created
    pending_question_list = []  # TODO: Add when Q&A model is created
    
    # Recent Activity
    recent_users = User.query.order_by(desc(User.created_at)).limit(8).all()
    recent_companies = Company.query.order_by(desc(Company.created_at)).limit(8).all()
    
    # Website Analytics Summary
    website_stats = {
        'total_users': total_users,
        'total_companies': total_companies,
        'total_subscribers': total_subscribers,
        'total_blogs': total_blogs,
        'pending_questions': pending_questions,
        'admin_users': admin_users,
        'subscriber_users': subscriber_users,
        'viewer_users': viewer_users
    }
    
    # Monthly Growth Data (last 6 months for cleaner display)
    monthly_data = []
    for i in range(6):
        month_start = (datetime.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        users_count = User.query.filter(
            User.created_at >= month_start,
            User.created_at <= month_end
        ).count()
        
        companies_count = Company.query.filter(
            Company.created_at >= month_start,
            Company.created_at <= month_end
        ).count()
        
        try:
            subscribers_count = NewsletterSubscriber.query.filter(
                NewsletterSubscriber.subscribed_at >= month_start,
                NewsletterSubscriber.subscribed_at <= month_end
            ).count()
        except:
            subscribers_count = 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'users': users_count,
            'companies': companies_count,
            'subscribers': subscribers_count
        })
    
    monthly_data.reverse()  # Show oldest to newest
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         admin_users=admin_users,
                         subscriber_users=subscriber_users,
                         viewer_users=viewer_users,
                         new_users_30d=new_users_30d,
                         active_users_30d=active_users_30d,
                         total_companies=total_companies,
                         new_companies_30d=new_companies_30d,
                         active_companies=active_companies,
                         total_subscribers=total_subscribers,
                         new_subscribers_30d=new_subscribers_30d,
                         total_campaigns=total_campaigns,
                         total_blogs=total_blogs,
                         pending_questions=pending_questions,
                         recent_campaigns=recent_campaigns,
                         recent_users=recent_users,
                         recent_companies=recent_companies,
                         recent_blogs=recent_blogs,
                         pending_question_list=pending_question_list,
                         website_stats=website_stats,
                         monthly_data=monthly_data)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage all users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    if search:
        query = query.filter(
            User.username.contains(search) |
            User.email.contains(search) |
            User.first_name.contains(search) |
            User.last_name.contains(search)
        )
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    # Store username for confirmation message
    username = user.username
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    """Manage all companies"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Company.query
    if search:
        query = query.filter(Company.company_name.contains(search))
    
    companies = query.order_by(desc(Company.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/companies.html', companies=companies, search=search)

# Note: User and Company models don't have is_active attributes
# These toggle functions are disabled until the models are updated

# @admin_bp.route('/toggle-user-status/<int:user_id>', methods=['POST'])
# @login_required
# @admin_required
# def toggle_user_status(user_id):
#     """Toggle user active status"""
#     user = User.query.get_or_404(user_id)
#     user.is_active = not user.is_active
#     db.session.commit()
#     
#     status = "activated" if user.is_active else "deactivated"
#     flash(f'User {user.username} has been {status}.', 'success')
#     
#     return redirect(url_for('admin.users'))

# @admin_bp.route('/toggle-company-status/<int:company_id>', methods=['POST'])
# @login_required
# @admin_required
# def toggle_company_status(company_id):
#     """Toggle company active status"""
#     company = Company.query.get_or_404(company_id)
#     company.is_active = not company.is_active
#     db.session.commit()
#     
#     status = "activated" if company.is_active else "deactivated"
#     flash(f'Company {company.name} has been {status}.', 'success')
#     
#     return redirect(url_for('admin.companies')) 