from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional

class SettingsForm(FlaskForm):
    # Profile Information
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    
    # Preferences
    email_notifications = BooleanField('Email Notifications')
    dark_mode = BooleanField('Dark Mode')
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German')
    ])
    
    # Password Change
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('new_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Save Settings') 