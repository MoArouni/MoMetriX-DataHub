# To be implemented later
# This file will contain email sending functionality for:
# - Password reset emails
# - Company invitations
# - Notifications

from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from app import mail
import smtplib
import logging

logger = logging.getLogger(__name__)

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except smtplib.SMTPAuthenticationError:
            logger.error("Email authentication failed. Please check your MAIL_USERNAME and MAIL_PASSWORD environment variables.")
        except smtplib.SMTPSenderRefused:
            logger.error("Sender address refused. Make sure your email account allows sending from this address.")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

def send_email(to, subject, template, **kwargs):
    """
    Send an email
    
    Args:
        to: Recipient email address
        subject: Email subject
        template: The template to use (without extension)
        **kwargs: Template variables
    """
    app = current_app._get_current_object()
    
    # If mail sending is suppressed, just log and return
    if app.config.get('MAIL_SUPPRESS_SEND', False):
        logger.info(f"Email sending suppressed: To: {to}, Subject: {subject}")
        return None
    
    # Make sure we have credentials
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        logger.warning("Email sending failed: MAIL_USERNAME or MAIL_PASSWORD not set")
        return None
    
    msg = Message(
        subject=app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['MAIL_SENDER'],
        recipients=[to]
    )
    
    try:
        msg.body = render_template(template + '.txt', **kwargs)
        msg.html = render_template(template + '.html', **kwargs)
    except Exception as e:
        logger.error(f"Failed to render email template: {str(e)}")
        return None
    
    # Send email asynchronously
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

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