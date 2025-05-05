from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.tool import Tool
from app.models.company import Company
from app.models.blog import BlogPost
from app.models.qa import Question, Answer
from app.models.user import User
from app.forms.company import CompanyForm
from datetime import datetime, timedelta

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
    """User dashboard page"""
    if current_user.is_admin:
        # Get stats for admin dashboard
        stats = {
            'users': User.query.count(),
            'companies': Company.query.count(),
            'questions': Question.query.count(),
            'blog_posts': BlogPost.query.count()
        }
        
        # Get recent users, companies, questions, and blog posts
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_companies = Company.query.order_by(Company.created_at.desc()).limit(5).all()
        recent_questions = Question.query.order_by(Question.created_at.desc()).limit(5).all()
        recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
        
        return render_template(
            'dashboard/admin_dashboard.html',
            stats=stats,
            recent_users=recent_users,
            recent_companies=recent_companies,
            recent_questions=recent_questions,
            recent_posts=recent_posts
        )
    else:
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
        
        # Get tools, recent blog posts, and questions
        user_tools = Tool.query.filter_by(creator_id=current_user.id).all()
        recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
        recent_questions = Question.query.order_by(Question.created_at.desc()).limit(5).all()
        
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
            user_tools=user_tools,
            company_tools=company_tools,
            recent_posts=recent_posts,
            recent_questions=recent_questions
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
        company = Company(
            company_name=form.company_name.data,
            company_email=form.company_email.data,
            phone=form.phone.data,
            admin_id=current_user.id
        )
        db.session.add(company)
        db.session.commit()
        
        # Update the user's company_id and company_role
        current_user.company_id = company.id
        current_user.role_company = 'admin'  # Creator becomes admin
        db.session.commit()
        
        flash('Company created successfully!', 'success')
        return redirect(url_for('dashboard.dashboard'))
        
    return render_template('dashboard/create_company.html', form=form) 