from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, TextAreaField, SelectField, BooleanField, FieldList, FormField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from datetime import date
from app.models.product import Product
from app.models.store import Store
import json

class SaleItemForm(FlaskForm):
    """Form for a single sale item"""
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = DecimalField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    unit_price = DecimalField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
    discount_percentage = DecimalField('Discount %', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    tax_percentage = DecimalField('Tax %', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    is_combo = BooleanField('Is Combo Product', default=False)
    
    # This field will be shown/hidden via JavaScript depending on is_combo
    combo_details = TextAreaField('Combo Details', validators=[Optional()])
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(SaleItemForm, self).__init__(*args, **kwargs)
        if company_id:
            # Dynamically load products for this company
            self.product_id.choices = [
                (prod.id, f"{prod.name} (£{prod.base_price:.2f})") 
                for prod in Product.query.filter_by(company_id=company_id, active=True).order_by(Product.name).all()
            ]

class SaleForm(FlaskForm):
    """Form for creating and editing a sale"""
    sale_date = DateField('Sale Date', validators=[DataRequired()], default=date.today)
    location = SelectField('Location', validators=[Optional()])
    cash_amount = DecimalField('Cash Amount', validators=[Optional(), NumberRange(min=0)], default=0)
    card_amount = DecimalField('Card Amount', validators=[Optional(), NumberRange(min=0)], default=0)
    total_amount = DecimalField('Total Amount', validators=[DataRequired(), NumberRange(min=0)], render_kw={'readonly': True})
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    
    # This will be a dynamic list of items, managed by JavaScript
    items = FieldList(FormField(SaleItemForm), min_entries=1)
    
    submit = SubmitField('Save Sale')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        if company_id:
            # Load locations for this company
            self.location.choices = [('', '-- Select Location --')] + [
                (str(loc.id), loc.name) 
                for loc in Store.query.filter_by(company_id=company_id).order_by(Store.name).all()
            ]
            # Add "Online" option if not already present
            self.location.choices.append(('online', 'Online'))

class StoreForm(FlaskForm):
    """Form for creating and editing store locations"""
    name = StringField('Store Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    submit = SubmitField('Save Store') 