from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from wtforms.widgets import TextArea

class NewsletterSubscribeForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Subscribe')

class NewsletterCampaignForm(FlaskForm):
    title = StringField('Campaign Title', validators=[DataRequired(), Length(max=200)])
    subject = StringField('Email Subject', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Email Content (Plain Text)', validators=[DataRequired()], 
                           render_kw={"rows": 10, "placeholder": "Enter the plain text version of your email..."})
    html_content = TextAreaField('HTML Content (Optional)', validators=[Optional()],
                                render_kw={"rows": 15, "placeholder": "Enter HTML version of your email (optional)..."})
    submit = SubmitField('Create Campaign')

class NewsletterTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    html_template = TextAreaField('HTML Template', validators=[DataRequired()],
                                 render_kw={"rows": 20, "placeholder": "Enter your HTML template..."})
    is_default = SelectField('Set as Default', choices=[('0', 'No'), ('1', 'Yes')], default='0')
    submit = SubmitField('Save Template') 