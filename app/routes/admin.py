from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, login_required
from app.models.user import User
from app.models.company import Company
from app.forms.auth_forms import LoginForm
from app.utils.decorators import admin_required
from app import db
from datetime import datetime
from app.config import Config

# Create admin blueprint with a complex URL prefix to hide it
admin_bp = Blueprint('admin', __name__, url_prefix='/adminr0ute$S19ou4w91048')

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Secret admin login route"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('dashboard.index'))
        
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
                    next_page = url_for('dashboard.index')
                return redirect(next_page)
            else:
                flash('This account does not have administrator privileges.', 'error')
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('admin/login.html', form=form)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Admin page to manage users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users.items, pagination=users)

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    """Admin page to manage companies"""
    page = request.args.get('page', 1, type=int)
    companies = Company.query.order_by(Company.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/companies.html', companies=companies.items, pagination=companies) 