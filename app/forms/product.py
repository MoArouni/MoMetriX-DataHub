from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models.product import Product
from app.models.product_category import ProductCategory

class ProductCategoryForm(FlaskForm):
    """Form for creating and editing product categories"""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    submit = SubmitField('Save Category')

class ProductForm(FlaskForm):
    """Form for creating and editing products"""
    name = StringField('Product Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    base_price = DecimalField('Base Price', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    active = BooleanField('Active', default=True)
    submit = SubmitField('Save Product')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        if company_id:
            # Dynamically load categories for this company
            self.category_id.choices = [
                (0, '-- No Category --')
            ] + [
                (cat.id, cat.name) 
                for cat in ProductCategory.query.filter_by(company_id=company_id).order_by(ProductCategory.name).all()
            ]
            
    def validate_category_id(self, field):
        """Convert 0 to None for the database"""
        if field.data == 0:
            field.data = None 