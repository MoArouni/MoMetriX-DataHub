from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    """Contact form for sending messages to the site admin"""
    name = StringField('Name', validators=[DataRequired(), Length(1, 64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(1, 128)])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message') 