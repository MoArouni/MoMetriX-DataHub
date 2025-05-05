from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, TextAreaField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.models.product_category import ProductCategory
from app.models.schema import CompanySchema

class SchemaFieldForm(FlaskForm):
    """Form for creating and editing schema fields"""
    field_name = StringField('Field Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    field_type = SelectField('Field Type', choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select (Dropdown)'),
        ('checkbox', 'Checkbox'),
        ('date', 'Date'),
        ('color', 'Color Picker'),
        ('textarea', 'Text Area'),
        ('radio', 'Radio Buttons')
    ], validators=[DataRequired()])
    category_id = SelectField('Apply to Category', coerce=int, validators=[Optional()])
    is_required = BooleanField('Required Field', default=True)
    default_value = StringField('Default Value', validators=[Optional(), Length(max=255)])
    options = TextAreaField('Options (for Select/Radio - one per line)', validators=[Optional()])
    display_order = IntegerField('Display Order', default=0, validators=[Optional()])
    submit = SubmitField('Save Field')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(SchemaFieldForm, self).__init__(*args, **kwargs)
        if company_id:
            # Dynamically load categories for this company
            self.category_id.choices = [
                (0, '-- All Categories --')
            ] + [
                (cat.id, cat.name) 
                for cat in ProductCategory.query.filter_by(company_id=company_id).order_by(ProductCategory.name).all()
            ]
            
    def validate_category_id(self, field):
        """Convert 0 to None for the database (applies to all categories)"""
        if field.data == 0:
            field.data = None

class CategoryForm(FlaskForm):
    """Form for creating product categories"""
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=100)])

class StoreForm(FlaskForm):
    """Form for creating store locations"""
    name = StringField('Store Name', validators=[DataRequired(), Length(min=2, max=100)])

class DatabaseSetupForm(FlaskForm):
    """Form for setting up the database structure"""
    categories = FieldList(FormField(CategoryForm), min_entries=1, max_entries=20)
    locations = FieldList(FormField(StoreForm), min_entries=1, max_entries=10)
    submit = SubmitField('Save Database Structure')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(DatabaseSetupForm, self).__init__(*args, **kwargs)
        self.company_id = company_id

class DynamicProductForm(FlaskForm):
    """Dynamic product data entry form"""
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=100)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    base_price = StringField('Base Price', validators=[DataRequired()])
    submit = SubmitField('Save Product')
    
    def __init__(self, company_id=None, category_id=None, *args, **kwargs):
        super(DynamicProductForm, self).__init__(*args, **kwargs)
        self.company_id = company_id
        
        if company_id:
            # Load categories for this company
            self.category_id.choices = [
                (cat.id, cat.name)
                for cat in ProductCategory.query.filter_by(company_id=company_id).order_by(ProductCategory.name).all()
            ]
            
            # If a category is specified, pre-select it
            if category_id:
                self.category_id.data = category_id
                
                # Add dynamic fields for this category
                schema_fields = CompanySchema.query.filter(
                    (CompanySchema.company_id == company_id) & 
                    ((CompanySchema.category_id == category_id) | (CompanySchema.category_id == None))
                ).order_by(CompanySchema.display_order).all()
                
                # Dynamically add form fields based on schema
                for field in schema_fields:
                    field_id = f"field_{field.schema_id}"
                    
                    if field.field_type == 'text':
                        setattr(self, field_id, StringField(
                            field.field_name, 
                            validators=[Length(max=255)] + 
                                        ([DataRequired()] if field.is_required else []),
                            default=field.default_value
                        ))
                    elif field.field_type == 'number':
                        setattr(self, field_id, StringField(
                            field.field_name,
                            validators=[Optional()],
                            default=field.default_value
                        ))
                    elif field.field_type in ('select', 'radio'):
                        choices = []
                        if field.options:
                            for option in field.options.splitlines():
                                option = option.strip()
                                if option:
                                    choices.append((option, option))
                                    
                        setattr(self, field_id, SelectField(
                            field.field_name,
                            choices=choices,
                            validators=[Optional()] + 
                                      ([DataRequired()] if field.is_required else []),
                            default=field.default_value if field.default_value else None
                        ))
                    elif field.field_type == 'checkbox':
                        setattr(self, field_id, BooleanField(
                            field.field_name,
                            default=True if field.default_value == 'true' else False
                        ))
                    elif field.field_type == 'textarea':
                        setattr(self, field_id, TextAreaField(
                            field.field_name,
                            validators=[Optional()] + 
                                      ([DataRequired()] if field.is_required else []),
                            default=field.default_value
                        ))
                    elif field.field_type == 'date':
                        setattr(self, field_id, StringField(
                            field.field_name,
                            validators=[Optional()] + 
                                      ([DataRequired()] if field.is_required else []),
                            default=field.default_value
                        ))
                    elif field.field_type == 'color':
                        setattr(self, field_id, StringField(
                            field.field_name,
                            validators=[Optional()] + 
                                      ([DataRequired()] if field.is_required else []),
                            default=field.default_value or '#000000'
                        ))
                        
    def get_dynamic_fields(self):
        """Returns a dictionary of dynamic field values"""
        dynamic_fields = {}
        for name, field in self._fields.items():
            if name.startswith('field_'):
                field_id = int(name.split('_')[1])
                if field.data is not None:
                    dynamic_fields[name] = field.data
        return dynamic_fields 