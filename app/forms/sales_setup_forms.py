from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FieldList, FormField, SubmitField, TextAreaField, EmailField, TelField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Length, Optional, Email, ValidationError

class CompanySetupForm(FlaskForm):
    """Form for setting up company details in the sales setup wizard"""
    company_name = StringField('Company Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message="Company name must be between 2 and 100 characters")
    ])
    company_email = EmailField('Company Email', validators=[
        DataRequired(),
        Email(),
        Length(max=100, message="Email must be less than 100 characters")
    ])
    phone = TelField('Phone Number', validators=[
        Length(max=20, message="Phone number must be less than 20 characters")
    ])
    submit = SubmitField('Save Company Details')

class StoreForm(FlaskForm):
    """Form for a single store"""
    name = StringField('Store Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message="Store name must be between 1 and 100 characters")
    ])
    
    # Disable CSRF for subforms
    class Meta:
        csrf = False

class StoresSetupForm(FlaskForm):
    """Form for setting up stores"""
    num_stores = IntegerField('Number of Stores', validators=[
        DataRequired(),
        NumberRange(min=1, message="You must have at least one store")
    ])
    stores = FieldList(FormField(StoreForm), min_entries=0)
    submit = SubmitField('Save Stores')

class CategoryForm(FlaskForm):
    """Form for a single category"""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message="Category name must be between 1 and 100 characters")
    ])
    
    # Disable CSRF for subforms
    class Meta:
        csrf = False

class CategoriesSetupForm(FlaskForm):
    """Form for setting up product categories"""
    num_categories = IntegerField('Number of Categories', validators=[
        DataRequired(),
        NumberRange(min=1, message="You must have at least one category")
    ])
    categories = FieldList(FormField(CategoryForm), min_entries=0)
    submit = SubmitField('Save Categories')

class ProductForm(FlaskForm):
    """Form for a single product"""
    name = StringField('Product Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message="Product name must be between 1 and 100 characters")
    ])
    
    # Disable CSRF for subforms
    class Meta:
        csrf = False

class ProductsSetupForm(FlaskForm):
    """Form for setting up products within a category"""
    category_id = IntegerField('Category ID', validators=[DataRequired()])
    num_products = IntegerField('Number of Products', validators=[
        DataRequired(),
        NumberRange(min=1, message="You must have at least one product")
    ])
    products = FieldList(FormField(ProductForm), min_entries=0)
    submit = SubmitField('Save Products')

class SaleEntryForm(FlaskForm):
    """Form for entering a new sale"""
    store_id = IntegerField('Store', validators=[DataRequired()])
    product_id = IntegerField('Product', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=1, message="Quantity must be at least 1")
    ])
    total_price = DecimalField('Total Price (£)', places=2, validators=[
        DataRequired(),
        NumberRange(min=0.01, message="Price must be greater than 0")
    ])
    cash_amount = DecimalField('Cash Amount (£)', places=2, default=0)
    card_amount = DecimalField('Card Amount (£)', places=2, default=0)
    notes = StringField('Notes', validators=[Length(max=500)])
    
    # Dynamic feature fields will be added programmatically
    submit = SubmitField('Record Sale')
    
    def validate_card_amount(self, field):
        """Validate that cash + card equals total price"""
        if hasattr(self, 'cash_amount') and hasattr(self, 'total_price'):
            total_payment = (self.cash_amount.data or 0) + (field.data or 0)
            total_price = self.total_price.data or 0
            
            if abs(total_payment - total_price) > 0.01:  # Allow for small rounding errors
                raise ValidationError(f"Total payment (£{total_payment:.2f}) must equal the total price (£{total_price:.2f})") 