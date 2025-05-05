from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app import db
from app.models.user import User
from app.models.roles import RoleWebsite, RoleCompany
from app.forms.auth_forms import LoginForm, RegistrationForm, PasswordResetRequestForm
from app.forms.auth_forms import ChangePasswordForm, PasswordResetForm, UpgradeRoleForm, CompanyRoleForm
from app.utils.email import send_password_reset_email

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html', form=form)
    
@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('dashboard.index'))
    
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if any users exist
        is_first_user = User.query.first() is None
        
        user = User(
            email=form.email.data.lower(),
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_admin=is_first_user,  # Set admin flag if first user
            role_website='admin' if is_first_user else 'subscriber'
        )
        user.password = form.password.data
            
        # Use the save method to enforce admin validation
        user.save()
        
        if is_first_user:
            flash('Your account has been created as the administrator.', 'success')
        else:
            flash('Your account has been created. You can now login.', 'success')
        
        # If subscriber, redirect to company creation
        if user.role_website == 'subscriber':
            # Log the user in
            login_user(user)
            flash('Please create your company to continue.', 'info')
            return redirect(url_for('dashboard.create_company'))
        else:
            return redirect(url_for('auth.login'))
            
    return render_template('auth/register.html', form=form)

@auth_bp.route('/upgrade-role', methods=['GET', 'POST'])
@login_required
def upgrade_role():
    """Upgrade user role route"""
    form = UpgradeRoleForm()
    
    if form.validate_on_submit():
        new_role = form.role_website.data
        
        # Only process if role is actually changing
        if new_role != current_user.role_website:
            # Update role
            current_user.role_website = new_role
            db.session.commit()
            
            if new_role == 'subscriber':
                flash('Your account has been upgraded to Subscriber status.', 'success')
                return redirect(url_for('dashboard.create_company'))
            else:
                flash('Your account role has been updated to Viewer.', 'success')
                return redirect(url_for('dashboard.index'))
        else:
            flash('No change in role detected.', 'info')
            
    return render_template('auth/upgrade_role.html', form=form)

@auth_bp.route('/company-role', methods=['GET', 'POST'])
@login_required
def company_role():
    """Manage company role"""
    # Ensure user is part of a company
    if not current_user.company_id:
        flash('You need to be part of a company first.', 'warning')
        return redirect(url_for('dashboard.index'))
        
    form = CompanyRoleForm()
    
    if form.validate_on_submit():
        new_role = form.role_company.data
        
        # Only process if role is actually changing
        if new_role != current_user.role_company:
            current_user.role_company = new_role
            db.session.commit()
            flash('Your company role has been updated.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('No change in role detected.', 'info')
            
    return render_template('auth/company_role.html', form=form)
    
@auth_bp.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    """Password reset request route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            send_password_reset_email(user)
        flash('An email with instructions to reset your password has been sent to you.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)
    
@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """Password reset route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    user = User.verify_reset_token(token)
    if user is None:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.password_reset_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password route"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid old password.', 'error')
    return render_template('auth/change_password.html', form=form)
