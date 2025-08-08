from flask import Blueprint, render_template, flash, redirect, request, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.forms.settings import SettingsForm
from app import db

settings = Blueprint('settings', __name__)

@settings.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    # Redirect company admins to the dedicated company admin settings
    if current_user.company_id and current_user.role_company == 'admin':
        return redirect(url_for('company_admin.settings'))
    
    # Regular user settings (personal preferences)
    form = SettingsForm()
    if form.validate_on_submit():
        # Update profile information
        current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        # Update preferences
        current_user.email_notifications = form.email_notifications.data
        current_user.dark_mode = form.dark_mode.data
        current_user.language = form.language.data
        
        # Handle password change
        if form.current_password.data and form.new_password.data:
            if check_password_hash(current_user.password_hash, form.current_password.data):
                current_user.password_hash = generate_password_hash(form.new_password.data)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'error')
                return render_template('user/settings.html', form=form)
        
        db.session.commit()
        flash('Your settings have been updated!', 'success')
        return redirect(url_for('settings.index'))
        
    elif request.method == 'GET':
        # Pre-populate form with current user data
        form.username.data = current_user.username
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email_notifications.data = current_user.email_notifications
        form.dark_mode.data = current_user.dark_mode
        form.language.data = current_user.language
        
    return render_template('user/settings.html', form=form) 