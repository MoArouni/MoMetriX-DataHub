from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, current_user, login_required
from datetime import datetime

from app import db
from app.models.user import User
from app.models.company import Company
from app.models.join_request import EmailVerificationCode, JoinRequest, ModeratorInvite, DirectModeratorInvite
from app.forms.join_request_forms import (
    EmailVerificationForm, VerifyCodeForm, CompanySelectionForm,
    ModeratorRegistrationForm, InviteAcceptanceForm
)
from app.utils.email import (
    send_verification_code_email, send_join_request_notification,
    send_join_request_declined_email, send_moderator_invite_email
)

# Create blueprint
join_request_bp = Blueprint('join_request', __name__, url_prefix='/join')

@join_request_bp.route('/', methods=['GET', 'POST'])
def start():
    """Start the join request process with email verification"""
    if current_user.is_authenticated:
        flash('You are already logged in. Please logout to join a different company.', 'info')
        return redirect(url_for('dashboard.index'))
    
    form = EmailVerificationForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        
        # Check if there's already a pending join request for this email
        existing_request = JoinRequest.query.filter_by(
            email=email,
            status='pending'
        ).first()
        
        if existing_request:
            flash('You already have a pending join request. Please wait for admin approval.', 'warning')
            return redirect(url_for('join_request.start'))
        
        # Clean up old verification codes for this email
        old_codes = EmailVerificationCode.query.filter_by(email=email).all()
        for code in old_codes:
            db.session.delete(code)
        
        # Create new verification code
        verification = EmailVerificationCode(email)
        db.session.add(verification)
        db.session.commit()
        
        # Send verification email
        try:
            result = send_verification_code_email(email, verification.code)
            if result is None or result is False:
                flash('Error sending verification email. Please check your email configuration.', 'error')
                return render_template('join_request/start.html', form=form)
        except Exception as e:
            flash(f'Error sending verification email: {str(e)}', 'error')
            return render_template('join_request/start.html', form=form)
        
        # Store email in session for next step
        session['join_email'] = email
        flash('A verification code has been sent to your email address.', 'success')
        return redirect(url_for('join_request.verify_email'))
    
    return render_template('join_request/start.html', form=form)

@join_request_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Verify the email with the sent code"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    email = session.get('join_email')
    if not email:
        flash('Please start the join process from the beginning.', 'error')
        return redirect(url_for('join_request.start'))
    
    form = VerifyCodeForm()
    form.email.data = email
    
    if form.validate_on_submit():
        current_app.logger.info(f"Verifying code {form.verification_code.data} for email {email}")
        
        # Check if code exists and is valid
        verification = EmailVerificationCode.query.filter_by(
            email=email.lower(),
            code=form.verification_code.data,
            is_used=False
        ).first()
        
        if verification:
            current_app.logger.info(f"Found verification code. Is valid: {verification.is_valid}, Is expired: {verification.is_expired}")
            
            if verification.is_valid:
                verification.mark_as_used()
                session['join_email_verified'] = True
                current_app.logger.info(f"Email verification successful for {email}")
                flash('Email verified successfully!', 'success')
                return redirect(url_for('join_request.select_company'))
            else:
                current_app.logger.info(f"Verification code expired for {email}")
                flash('Verification code has expired. Please request a new one.', 'error')
        else:
            current_app.logger.info(f"No valid verification code found for {email} with code {form.verification_code.data}")
            flash('Invalid verification code. Please try again.', 'error')
    
    return render_template('join_request/verify_email.html', form=form, email=email)

@join_request_bp.route('/select-company', methods=['GET', 'POST'])
def select_company():
    """Select company and submit join request"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    email = session.get('join_email')
    email_verified = session.get('join_email_verified')
    
    if not email or not email_verified:
        flash('Please complete email verification first.', 'error')
        return redirect(url_for('join_request.start'))
    
    form = CompanySelectionForm()
    form.email.data = email
    
    if form.validate_on_submit():
        if form.company_id.data == 0:
            flash('Please select a company.', 'error')
            return render_template('join_request/select_company.html', form=form)
        
        # Create join request with user information
        join_request = JoinRequest(
            email=email,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            company_id=form.company_id.data,
            message=form.message.data
        )
        db.session.add(join_request)
        db.session.commit()
        
        # Notify company admin
        company = Company.query.get(form.company_id.data)
        if company and company.admin:
            send_join_request_notification(join_request, company.admin)
        
        # Clear session data
        session.pop('join_email', None)
        session.pop('join_email_verified', None)
        
        flash('Your join request has been submitted successfully! You will receive an email when it is reviewed.', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('join_request/select_company.html', form=form)

@join_request_bp.route('/accept-invite/<token>', methods=['GET', 'POST'])
def accept_invite(token):
    """Accept moderator invite with passcode"""
    if current_user.is_authenticated:
        flash('Please logout before accepting an invite.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    form = InviteAcceptanceForm()
    form.invite_token.data = token
    
    if form.validate_on_submit():
        invite = ModeratorInvite.verify_invite(token, form.passcode.data)
        if invite:
            # Store invite info in session for registration
            session['invite_token'] = token
            session['invite_email'] = invite.email
            session['invite_company_id'] = invite.company_id
            session['invite_permissions'] = invite.role_permissions
            
            flash('Invite verified! Please complete your registration.', 'success')
            return redirect(url_for('join_request.complete_registration'))
        else:
            flash('Invalid or expired invite token/passcode.', 'error')
    
    return render_template('join_request/accept_invite.html', form=form, token=token)

@join_request_bp.route('/complete-registration', methods=['GET', 'POST'])
def complete_registration():
    """Complete moderator registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    invite_token = session.get('invite_token')
    invite_email = session.get('invite_email')
    invite_company_id = session.get('invite_company_id')
    invite_permissions = session.get('invite_permissions')
    
    if not all([invite_token, invite_email, invite_company_id, invite_permissions]):
        flash('Invalid registration session. Please use the invite link again.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get the invite and join request to pre-populate user information
    invite = ModeratorInvite.query.filter_by(invite_token=invite_token).first()
    if not invite or not invite.join_request:
        flash('Invalid invite. Please use the invite link again.', 'error')
        return redirect(url_for('dashboard.index'))
    
    join_request = invite.join_request
    
    form = ModeratorRegistrationForm()
    form.email.data = invite_email
    form.invite_token.data = invite_token
    
    # Pre-populate form with data from join request
    if request.method == 'GET':
        form.first_name.data = join_request.first_name
        form.last_name.data = join_request.last_name
        form.username.data = join_request.username
    
    if form.validate_on_submit():
        # Create the user with role_website='viewer' and role_company='moderator'
        user = User(
            email=invite_email,
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role_website='viewer',  # User is viewer at website level
            company_id=invite_company_id,
            role_company='moderator'  # User is moderator at company level
        )
        user.password = form.password.data
        
        db.session.add(user)
        
        # Mark invite as used
        invite.mark_as_used()
        
        db.session.commit()
        
        # Clear session data
        for key in ['invite_token', 'invite_email', 'invite_company_id', 'invite_permissions']:
            session.pop(key, None)
        
        # Log the user in
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash('Registration completed successfully! Welcome to the team.', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('join_request/complete_registration.html', 
                         form=form, 
                         email=invite_email,
                         permissions=invite_permissions,
                         company_name=join_request.company.company_name)

@join_request_bp.route('/accept-direct-invite/<token>', methods=['GET', 'POST'])
def accept_direct_invite(token):
    """Accept direct moderator invite"""
    if current_user.is_authenticated:
        flash('Please logout before accepting an invite.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Find the direct invite
    invite = DirectModeratorInvite.query.filter_by(invite_token=token).first()
    if not invite or not invite.is_valid:
        flash('Invalid or expired invite link.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Check if email is already registered
    existing_user = User.query.filter_by(email=invite.email).first()
    if existing_user:
        flash('This email is already registered. Please login to your existing account.', 'error')
        return redirect(url_for('auth.login'))
    
    form = ModeratorRegistrationForm()
    form.email.data = invite.email
    
    # Pre-populate form with data from invite
    if request.method == 'GET':
        form.first_name.data = invite.first_name
        form.last_name.data = invite.last_name
    
    if form.validate_on_submit():
        try:
            # Create the user with role_website='viewer' and role_company='moderator'
            user = User(
                email=invite.email,
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role_website='viewer',  # User is viewer at website level
                company_id=invite.company_id,
                role_company='moderator'  # User is moderator at company level
            )
            user.password = form.password.data
            
            db.session.add(user)
            
            # Mark invite as used
            invite.mark_as_used()
            
            db.session.commit()
            
            # Log the user in
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Registration completed successfully! Welcome to the team.', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error completing registration: {str(e)}', 'error')
    
    return render_template('join_request/accept_direct_invite.html', 
                         form=form, 
                         invite=invite,
                         company=invite.company)

@join_request_bp.route('/resend-code', methods=['POST'])
def resend_code():
    """Resend verification code"""
    email = session.get('join_email')
    if not email:
        flash('No email found in session.', 'error')
        return redirect(url_for('join_request.start'))
    
    # Clean up old codes
    old_codes = EmailVerificationCode.query.filter_by(email=email).all()
    for code in old_codes:
        db.session.delete(code)
    
    # Create new code
    verification = EmailVerificationCode(email)
    db.session.add(verification)
    db.session.commit()
    
    # Send email
    try:
        result = send_verification_code_email(email, verification.code)
        if result is None or result is False:
            flash('Error sending verification email. Please check your email configuration.', 'error')
            return redirect(url_for('join_request.verify_email'))
    except Exception as e:
        flash(f'Error sending verification email: {str(e)}', 'error')
        return redirect(url_for('join_request.verify_email'))
    
    flash('A new verification code has been sent to your email.', 'success')
    return redirect(url_for('join_request.verify_email'))

@join_request_bp.route('/test-email')
def test_email():
    """Test route to check email configuration"""
    try:
        # Check mail configuration
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_sender = current_app.config.get('MAIL_SENDER')
        
        config_status = {
            'MAIL_SERVER': mail_server,
            'MAIL_USERNAME': mail_username,
            'MAIL_PASSWORD': 'Set' if mail_password else 'Not Set',
            'MAIL_PORT': current_app.config.get('MAIL_PORT'),
            'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
            'MAIL_SENDER': mail_sender
        }
        
        # Test sending an email
        test_result = "Not tested"
        try:
            test_email = current_app.config.get('ADMIN_EMAIL', 'admin@example.com')
            result = send_verification_code_email(test_email, '123456')
            test_result = "SUCCESS" if result else "FAILED"
        except Exception as e:
            test_result = f"ERROR: {str(e)}"
        
        return f"""
        <h2>Email Configuration Status:</h2>
        <pre>{config_status}</pre>
        <h2>Email Test Result:</h2>
        <pre>{test_result}</pre>
        <p><a href="/join/">Back to Join Request</a></p>
        """
        
    except Exception as e:
        return f"<h2>Error checking email config:</h2><pre>{str(e)}</pre>" 