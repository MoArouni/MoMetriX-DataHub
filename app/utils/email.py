# To be implemented later
# This file will contain email sending functionality for:
# - Password reset emails
# - Company invitations
# - Notifications

from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from app import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

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
    msg = Message(
        subject=app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['MAIL_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    
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