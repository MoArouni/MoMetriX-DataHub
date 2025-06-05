from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app import db
from app.models.user import User
from app.models.roles import RoleWebsite, RoleCompany
from app.forms.auth_forms import LoginForm, RegistrationForm, PasswordResetRequestForm
from app.forms.auth_forms import ChangePasswordForm, PasswordResetForm, UpgradeRoleForm, CompanyRoleForm, ResendVerificationForm
from app.utils.email import send_password_reset_email, send_email_verification_email

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
            # Check if email is verified (except for admin users)
            if not user.email_verified and not user.is_admin:
                flash('Please verify your email address before logging in. Check your email for the verification link.', 'warning')
                return render_template('auth/login.html', form=form)
            
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
        
        # Send email verification for non-admin users
        if not user.is_admin:
            try:
                send_email_verification_email(user)
                flash('Your account has been created! Please check your email to verify your account before logging in.', 'success')
            except Exception as e:
                flash('Account created but email verification failed. Please contact support.', 'warning')
        else:
            # Admin users don't need email verification
            user.email_verified = True
            db.session.commit()
        
        if is_first_user:
            flash('Your account has been created as the administrator.', 'success')
        else:
            if user.email_verified:
                flash('Your account has been created. You can now login.', 'success')
        
        # If subscriber and email verified, redirect to company creation
        if user.role_website == 'subscriber' and user.email_verified:
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
        flash('Your password has been updated successfully. You can now login with your new password.', 'success')
        return redirect(url_for('auth.login'))
            
    return render_template('auth/password_reset.html', form=form, token=token)

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

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    user = User.verify_email_token(token)
    if user is None:
        flash('The email verification link is invalid or has expired.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Your email has already been verified. You can now login.', 'info')
        return redirect(url_for('auth.login'))
    
    user.verify_email()
    flash('Your email has been verified successfully! You can now login.', 'success')
    
    # If this is a subscriber, redirect to company creation after login
    if user.role_website == 'subscriber':
        login_user(user)
        flash('Please create your company to continue.', 'info')
        return redirect(url_for('dashboard.create_company'))
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend email verification"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = ResendVerificationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and not user.email_verified and not user.is_admin:
            try:
                # Generate new token
                token = user.generate_email_verification_token()
                db.session.commit()
                
                # Generate verification URL
                verification_url = url_for('auth.verify_email', token=token, _external=True)
                
                # Send email directly
                from app.utils.email import send_email
                result = send_email(
                    to=user.email,
                    subject='Verify Your Email Address',
                    template='auth/email/verify_email',
                    user=user,
                    verification_url=verification_url
                )
                
                # Check result
                if result is None:
                    flash('Email service is not configured. Please contact support.', 'error')
                    return render_template('auth/resend_verification.html', form=form)
                
                flash('A new verification email has been sent to your email address. Please check your inbox.', 'success')
                return redirect(url_for('auth.login'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error sending verification email. Please try again later or contact support.', 'error')
                return render_template('auth/resend_verification.html', form=form)
        else:
            # Security: don't reveal if email exists
            flash('If an account with this email exists and requires verification, a new verification email has been sent.', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/resend_verification.html', form=form)
