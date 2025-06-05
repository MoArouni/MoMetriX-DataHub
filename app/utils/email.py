# To be implemented later
# This file will contain email sending functionality for:
# - Password reset emails
# - Company invitations
# - Notifications

from flask import render_template, current_app, url_for
from flask_mail import Message
from threading import Thread
from app import mail
import logging

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            app.logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            app.logger.error(f"Failed to send email to {msg.recipients}: {str(e)}")
            raise e

def send_email(to, subject, template, **kwargs):
    """
    Send an email
    
    Args:
        to: Recipient email address
        subject: Email subject
        template: The template to use (without extension)
        **kwargs: Template variables
    """
    try:
        app = current_app._get_current_object()
        
        # Check if mail is configured
        if not app.config.get('MAIL_SERVER') or not app.config.get('MAIL_USERNAME'):
            app.logger.warning("Mail server or username not configured.")
            
            # In development mode, log the email content instead of sending
            if app.debug:
                app.logger.info("=== EMAIL DEBUG MODE ===")
                app.logger.info(f"TO: {to}")
                app.logger.info(f"SUBJECT: {app.config.get('MAIL_SUBJECT_PREFIX', '')} {subject}")
                
                try:
                    body = render_template(template + '.txt', **kwargs)
                    app.logger.info(f"BODY:\n{body}")
                except Exception as e:
                    app.logger.info(f"Could not render template {template}.txt: {str(e)}")
                
                try:
                    html = render_template(template + '.html', **kwargs)
                    app.logger.info(f"HTML:\n{html}")
                except Exception as e:
                    app.logger.info(f"Could not render template {template}.html: {str(e)}")
                
                app.logger.info("=== END EMAIL DEBUG ===")
                return True  # Return success in debug mode
            else:
                return None
            
        msg = Message(
            subject=app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
            sender=app.config['MAIL_SENDER'],
            recipients=[to]
        )
        
        # Try to render templates
        try:
            msg.body = render_template(template + '.txt', **kwargs)
            msg.html = render_template(template + '.html', **kwargs)
        except Exception as e:
            app.logger.error(f"Failed to render email template {template}: {str(e)}")
            # Fallback to plain text
            msg.body = f"Subject: {subject}\n\nThis is an automated message from MoMetriX DataHub."
        
        app.logger.info(f"Attempting to send email to {to} with subject: {subject}")
        
        # Send email asynchronously
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return thr
        
    except Exception as e:
        current_app.logger.error(f"Error in send_email function: {str(e)}")
        return None

def send_password_reset_email(user):
    """
    Send a password reset email to a user
    
    Args:
        user: User model instance
    """
    token = user.generate_reset_token()
    send_email(
        to=user.email,
        subject='Reset Your Password',
        template='auth/email/reset_password',
        user=user,
        token=token
    )

def send_verification_code_email(email, code):
    """
    Send email verification code
    
    Args:
        email: Email address
        code: 6-digit verification code
    """
    current_app.logger.info(f"Sending verification code {code} to {email}")
    
    result = send_email(
        to=email,
        subject='Email Verification Code',
        template='join_request/email/verification_code',
        email=email,
        code=code
    )
    
    if result is None:
        current_app.logger.error(f"Failed to send verification code to {email}")
        return False
    
    return True

def send_join_request_notification(join_request, admin_user):
    """
    Send notification to admin about new join request
    
    Args:
        join_request: JoinRequest model instance
        admin_user: Admin user to notify
    """
    send_email(
        to=admin_user.email,
        subject='New Moderator Join Request',
        template='join_request/email/admin_notification',
        join_request=join_request,
        admin_user=admin_user,
        review_url=url_for('company_admin.join_requests', _external=True)
    )

def send_join_request_declined_email(join_request):
    """
    Send notification to user about declined join request
    
    Args:
        join_request: JoinRequest model instance
    """
    send_email(
        to=join_request.email,
        subject=f'Join Request Declined - {join_request.company.company_name}',
        template='join_request/email/declined_notification',
        join_request=join_request,
        company=join_request.company
    )

def send_moderator_invite_email(invite):
    """
    Send moderator invite email with passcode
    
    Args:
        invite: ModeratorInvite model instance
    """
    invite_url = url_for('join_request.accept_invite', token=invite.invite_token, _external=True)
    
    send_email(
        to=invite.email,
        subject=f'Welcome to {invite.company.company_name} - Complete Your Registration',
        template='join_request/email/moderator_invite',
        invite=invite,
        company=invite.company,
        invite_url=invite_url,
        passcode=invite.passcode
    )

def send_direct_moderator_invite_email(invite):
    """
    Send direct moderator invite email
    
    Args:
        invite: DirectModeratorInvite model instance
    """
    invite_url = url_for('join_request.accept_direct_invite', token=invite.invite_token, _external=True)
    
    send_email(
        to=invite.email,
        subject=f'Invitation to Join {invite.company.company_name} as Moderator',
        template='join_request/email/direct_moderator_invite',
        invite=invite,
        company=invite.company,
        inviter=invite.inviter,
        invite_url=invite_url
    )

def send_email_verification_email(user):
    """
    Send email verification email for new user registration
    
    Args:
        user: User model instance
        
    Returns:
        Result from send_email function
    """
    try:
        # Generate token and save to database first
        token = user.generate_email_verification_token()
        
        # Import db here to avoid circular imports
        from app import db
        db.session.commit()
        
        # Generate verification URL
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        
        # Send the email
        return send_email(
            to=user.email,
            subject='Verify Your Email Address',
            template='auth/email/verify_email',
            user=user,
            verification_url=verification_url
        )
    except Exception as e:
        current_app.logger.error(f"Error in send_email_verification_email: {str(e)}")
        # Rollback any database changes if there was an error
        from app import db
        db.session.rollback()
        raise e 