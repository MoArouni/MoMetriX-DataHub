from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo, Optional
from app.models.user import User
from flask_login import current_user

class UserSettingsForm(FlaskForm):
    """Form for updating user settings"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message="Username must be between 3 and 64 characters")
    ])
    first_name = StringField('First Name', validators=[
        Optional(),
        Length(max=64, message="First name must be less than 64 characters")
    ])
    last_name = StringField('Last Name', validators=[
        Optional(),
        Length(max=64, message="Last name must be less than 64 characters")
    ])
    email_notifications = BooleanField('Email Notifications')
    dark_mode = BooleanField('Dark Mode')
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('de', 'German')
    ])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Save Changes')
    
    def validate_username(self, field):
        """Validate username is unique"""
        if field.data != current_user.username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Username already in use. Please choose a different one.')
    
    def validate_current_password(self, field):
        """Validate current password if changing password"""
        if self.new_password.data and not current_user.verify_password(field.data):
            raise ValidationError('Current password is incorrect.') 