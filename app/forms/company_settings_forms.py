from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, SelectMultipleField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from wtforms.widgets import ListWidget, CheckboxInput
from app.models.user import User
from app.models.store import Store

class MultiCheckboxField(SelectMultipleField):
    """A multiple-select field with checkboxes"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class CompanyDetailsForm(FlaskForm):
    """Form for updating company details"""
    company_name = StringField('Company Name', validators=[DataRequired(), Length(1, 100)])
    company_email = StringField('Company Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(0, 20)])
    address = TextAreaField('Business Address', validators=[Optional(), Length(0, 500)])
    industry = SelectField('Industry', choices=[
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('services', 'Services'),
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('food_beverage', 'Food & Beverage'),
        ('automotive', 'Automotive'),
        ('real_estate', 'Real Estate'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[Optional()])
    description = TextAreaField('Company Description', validators=[Optional(), Length(0, 1000)])
    submit = SubmitField('Update Company Details')

class UserPermissionsForm(FlaskForm):
    """Form for managing user permissions - 3 simple settings"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    
    # 1. What can they do
    access_level = SelectField('What can they do?', choices=[
        ('daily_sales', 'Add & See Daily Sales'),
        ('full_access', 'See Everything')
    ], validators=[DataRequired()])
    
    # 2. Date range for seeing data
    data_range = SelectField('Date range for seeing data', choices=[
        ('current_day', 'Current Day Only'),
        ('all_time', 'All Time')
    ], validators=[DataRequired()])
    
    # 3. Store access permissions
    allowed_stores = MultiCheckboxField('Which stores can they access?', coerce=int)
    
    submit = SubmitField('Update Permissions')
    
    def __init__(self, company_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate store choices
        stores = Store.query.filter_by(company_id=company_id).all()
        self.allowed_stores.choices = [(store.id, store.name) for store in stores]

class BulkUserPermissionsForm(FlaskForm):
    """Form for updating multiple users' permissions at once"""
    user_ids = HiddenField('User IDs')
    
    # Data range permissions
    data_range_access = SelectField('Sales Data Access Range', choices=[
        ('', 'No Change'),
        ('current_day', 'Current Day Only'),
        ('week', 'Past Week'),
        ('month', 'Past Month'),
        ('all_time', 'All Historical Data')
    ], validators=[Optional()])
    
    # Store access
    store_access_mode = SelectField('Store Access Mode', choices=[
        ('', 'No Change'),
        ('all', 'All Stores'),
        ('none', 'No Stores'),
        ('specific', 'Specific Stores')
    ], validators=[Optional()])
    
    allowed_stores = MultiCheckboxField('Specific Stores', coerce=int)
    
    # Batch permission updates
    update_view_sales = BooleanField('Update View Sales Permission')
    can_view_sales = BooleanField('Can View Sales Data')
    
    update_add_sales = BooleanField('Update Add Sales Permission')
    can_add_sales = BooleanField('Can Add Sales')
    
    update_analytics = BooleanField('Update Analytics Permission')
    can_view_analytics = BooleanField('Can View Analytics')
    
    submit = SubmitField('Update Selected Users')
    
    def __init__(self, company_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate store choices
        stores = Store.query.filter_by(company_id=company_id).all()
        self.allowed_stores.choices = [(store.id, store.name) for store in stores]

class CompanySettingsForm(FlaskForm):
    """Main company settings form combining all sections"""
    # Company details section
    company_name = StringField('Company Name', validators=[DataRequired(), Length(1, 100)])
    company_email = StringField('Company Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(0, 20)])
    
    # Notification settings
    email_notifications = BooleanField('Email Notifications for Join Requests')
    daily_reports = BooleanField('Daily Sales Report Emails')
    weekly_reports = BooleanField('Weekly Analytics Emails')
    
    # Data retention settings
    data_retention_days = IntegerField('Data Retention (Days)', 
                                     validators=[Optional(), NumberRange(min=30, max=3650)],
                                     default=365)
    
    submit = SubmitField('Save Settings') 