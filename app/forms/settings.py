from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired

class SettingsForm(FlaskForm):
    email_notifications = BooleanField('Email Notifications')
    dark_mode = BooleanField('Dark Mode')
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German')
    ])
    submit = SubmitField('Save Settings') 