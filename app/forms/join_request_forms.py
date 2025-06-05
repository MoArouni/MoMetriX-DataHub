from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User
from app.models.company import Company

class EmailVerificationForm(FlaskForm):
    """Form for email verification step"""
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    
    def validate_email(self, field):
        """Check if email is already registered"""
        user = User.query.filter_by(email=field.data.lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different email or login to your existing account.')

class VerifyCodeForm(FlaskForm):
    """Form for verifying the email code"""
    email = HiddenField()
    verification_code = StringField('Verification Code', validators=[
        DataRequired(message='Verification code is required.'),
        Length(min=6, max=6, message='Verification code must be 6 digits.')
    ])

class CompanySelectionForm(FlaskForm):
    """Form for selecting company and adding user information"""
    email = HiddenField()
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(min=2, max=64, message='First name must be between 2 and 64 characters.')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(min=2, max=64, message='Last name must be between 2 and 64 characters.')
    ])
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
    ])
    company_id = SelectField('Select Company', validators=[
        DataRequired(message='Please select a company.')
    ], coerce=int)
    message = TextAreaField('Message (Optional)', validators=[
        Length(max=500, message='Message cannot exceed 500 characters.')
    ])
    
    def __init__(self, *args, **kwargs):
        super(CompanySelectionForm, self).__init__(*args, **kwargs)
        # Populate company choices
        companies = Company.query.order_by(Company.company_name).all()
        self.company_id.choices = [(0, 'Select a company...')] + [
            (company.id, company.company_name) for company in companies
        ]
    
    def validate_username(self, field):
        """Check if username is already taken"""
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

class ModeratorRegistrationForm(FlaskForm):
    """Form for moderator registration after invite acceptance"""
    email = HiddenField()
    invite_token = HiddenField()
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(min=2, max=64, message='First name must be between 2 and 64 characters.')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(min=2, max=64, message='Last name must be between 2 and 64 characters.')
    ])
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    
    def validate_username(self, field):
        """Check if username is already taken"""
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

class InviteAcceptanceForm(FlaskForm):
    """Form for accepting invite with passcode"""
    invite_token = HiddenField()
    passcode = StringField('6-Digit Passcode', validators=[
        DataRequired(message='Passcode is required.'),
        Length(min=6, max=6, message='Passcode must be 6 digits.')
    ])

class AdminDirectInviteForm(FlaskForm):
    """Form for admin to directly invite moderators"""
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(min=2, max=64, message='First name must be between 2 and 64 characters.')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(min=2, max=64, message='Last name must be between 2 and 64 characters.')
    ])
    role_permissions = SelectField('Role Permissions', validators=[
        DataRequired(message='Please select role permissions.')
    ], choices=[
        ('', 'Select permissions...'),
        ('data_entry', 'Data Entry Only'),
        ('daily_sales', 'Data Entry + Daily Sales View'),
        ('full_view', 'Full Access (All Data)')
    ])
    message = TextAreaField('Welcome Message (Optional)', validators=[
        Length(max=500, message='Message cannot exceed 500 characters.')
    ])
    
    def validate_email(self, field):
        """Check if email is already registered"""
        user = User.query.filter_by(email=field.data.lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different email.')

class AdminJoinRequestForm(FlaskForm):
    """Form for admin to approve/decline join requests"""
    # No validation needed since we handle it manually in the template and backend
    pass 