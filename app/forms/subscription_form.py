from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models.mailing_list import MailingList

class SubscriptionForm(FlaskForm):
    """Subscription form for newsletter and updates"""
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message="Please enter a valid email address."),
        Length(1, 64)
    ])
    submit = SubmitField('Subscribe')
    
    def validate_email(self, field):
        """Check if email is already subscribed"""
        if MailingList.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already subscribed to our newsletter.') 

