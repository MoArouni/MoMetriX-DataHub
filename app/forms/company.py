from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models.company import Company

class CompanyForm(FlaskForm):
    """Form for creating and editing a company"""
    company_name = StringField('Company Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    company_email = EmailField('Company Email', validators=[
        DataRequired(),
        Email(),
        Length(max=100)
    ])
    phone = TelField('Phone Number', validators=[
        Length(max=20)
    ])
    submit = SubmitField('Create Company')
    
    def validate_company_name(self, field):
        """Validate company name is unique"""
        company = Company.query.filter_by(company_name=field.data).first()
        if company:
            raise ValidationError('Company name already in use.')
    
    def validate_company_email(self, field):
        """Validate company email is unique"""
        company = Company.query.filter_by(company_email=field.data).first()
        if company:
            raise ValidationError('Company email already in use.') 