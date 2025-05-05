from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.forms.user import UserSettingsForm
from app.models.user import User

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    form = UserSettingsForm()
    
    # Pre-populate the form with current user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email_notifications.data = current_user.email_notifications
        form.dark_mode.data = current_user.dark_mode
        form.language.data = current_user.language
    
    if form.validate_on_submit():
        # Save all form data
        current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email_notifications = form.email_notifications.data
        current_user.dark_mode = form.dark_mode.data
        current_user.language = form.language.data
        
        # Handle password change if provided
        if form.new_password.data:
            current_user.password = form.new_password.data
        
        # Save to database
        db.session.commit()
        flash('Your settings have been updated successfully!', 'success')
        return redirect(url_for('user.settings'))
    
    return render_template('user/settings.html', form=form)

@user_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('user/profile.html') 