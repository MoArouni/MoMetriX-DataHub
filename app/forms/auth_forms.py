from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError, RadioField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.models.user import User
from app.models.roles import RoleWebsite, RoleCompany

class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')
    
class RegistrationForm(FlaskForm):
    """User registration form"""
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 64)])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
    ])
    first_name = StringField('First Name', validators=[Length(0, 64)])
    last_name = StringField('Last Name', validators=[Length(0, 64)])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8),
    ])
    password2 = PasswordField('Confirm password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        """Validate email is not already registered"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
            
    def validate_username(self, field):
        """Validate username is not already in use"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
            
class PasswordResetRequestForm(FlaskForm):
    """Request password reset form"""
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 64)])
    submit = SubmitField('Reset Password')
    
class PasswordResetForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8)
    ])
    password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

class UpgradeRoleForm(FlaskForm):
    """Form for upgrading user role"""
    role_website = SelectField('New Website Role', 
                        choices=[
                            ('subscriber', 'Subscriber - Create your own company and access data tools')
                        ], 
                        validators=[DataRequired()])
    password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Upgrade Role')
    
    def validate_password(self, field):
        """Validate the user's password"""
        from flask_login import current_user
        if not current_user.verify_password(field.data):
            raise ValidationError('Incorrect password.')

class CompanyRoleForm(FlaskForm):
    """Form for managing company roles"""
    role_company = SelectField('Company Role', 
                        choices=[
                            ('admin', 'Administrator - Full control over company'),
                            ('moderator', 'Moderator - Limited management permissions')
                        ],
                        validators=[DataRequired()])
    submit = SubmitField('Update Role') 


class ChangePasswordForm(FlaskForm):
    """Form for changing user password"""
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')
