from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class StoreForm(FlaskForm):
    """Form for a single store"""
    name = StringField('Store Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message="Store name must be between 1 and 100 characters")
    ])

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
    cash_amount = IntegerField('Cash Amount (£)', default=0)
    card_amount = IntegerField('Card Amount (£)', default=0)
    notes = StringField('Notes', validators=[Length(max=500)])
    
    # Dynamic feature fields will be added programmatically
    submit = SubmitField('Record Sale') 