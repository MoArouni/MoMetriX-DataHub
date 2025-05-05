from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.schema import CompanySchema
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.store import Store
from app.forms.schema import SchemaFieldForm, DatabaseSetupForm, DynamicProductForm
from app.utils.decorators import company_required
import json

# Create blueprint
schema_bp = Blueprint('schema', __name__, url_prefix='/schema')

@schema_bp.route('/')
@login_required
@company_required
def index():
    """Show schema fields list"""
    fields = CompanySchema.query.filter_by(company_id=current_user.company_id).order_by(CompanySchema.field_name).all()
    return render_template('schema/index.html', fields=fields)

@schema_bp.route('/new', methods=['GET', 'POST'])
@login_required
@company_required
def new_field():
    """Create a new schema field"""
    form = SchemaFieldForm(company_id=current_user.company_id)
    
    if form.validate_on_submit():
        field = CompanySchema(
            company_id=current_user.company_id,
            field_name=form.field_name.data,
            field_type=form.field_type.data,
            category_id=form.category_id.data,
            is_required=form.is_required.data,
            default_value=form.default_value.data,
            options=form.options.data,
            display_order=form.display_order.data
        )
        db.session.add(field)
        db.session.commit()
        flash('Field created successfully!', 'success')
        return redirect(url_for('schema.index'))
        
    return render_template('schema/form.html', form=form, title='New Field')

@schema_bp.route('/edit/<int:schema_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_field(schema_id):
    """Edit an existing schema field"""
    field = CompanySchema.query.get_or_404(schema_id)
    
    # Ensure field belongs to user's company
    if field.company_id != current_user.company_id:
        flash('You do not have permission to edit this field.', 'danger')
        return redirect(url_for('schema.index'))
    
    form = SchemaFieldForm(company_id=current_user.company_id, obj=field)
    
    if form.validate_on_submit():
        form.populate_obj(field)
        db.session.commit()
        flash('Field updated successfully!', 'success')
        return redirect(url_for('schema.index'))
        
    return render_template('schema/form.html', form=form, title='Edit Field', field=field)

@schema_bp.route('/delete/<int:schema_id>', methods=['POST'])
@login_required
@company_required
def delete_field(schema_id):
    """Delete a schema field"""
    field = CompanySchema.query.get_or_404(schema_id)
    
    # Ensure field belongs to user's company
    if field.company_id != current_user.company_id:
        flash('You do not have permission to delete this field.', 'danger')
        return redirect(url_for('schema.index'))
    
    db.session.delete(field)
    db.session.commit()
    flash('Field deleted successfully!', 'success')
    return redirect(url_for('schema.index'))

# API endpoint to get schema fields for a category
@schema_bp.route('/api/fields')
@login_required
@company_required
def api_get_fields():
    """Get schema fields as JSON"""
    category_id = request.args.get('category_id', type=int)
    
    # Get fields that apply to all categories or the specific category
    query = CompanySchema.query.filter_by(company_id=current_user.company_id)
    
    if category_id:
        query = query.filter((CompanySchema.category_id == None) | (CompanySchema.category_id == category_id))
    else:
        query = query.filter(CompanySchema.category_id == None)
    
    fields = query.order_by(CompanySchema.field_name).all()
    
    return jsonify([{
        'schema_id': field.schema_id,
        'field_name': field.field_name,
        'field_type': field.field_type,
        'category_id': field.category_id,
        'is_required': field.is_required,
        'default_value': field.default_value,
        'options': field.options,
        'display_order': field.display_order
    } for field in fields])

@schema_bp.route('/setup', methods=['GET', 'POST'])
@login_required
@company_required
def database_setup():
    """Database structure setup form"""
    form = DatabaseSetupForm(company_id=current_user.company_id)
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        # Load existing categories
        categories = ProductCategory.query.filter_by(company_id=current_user.company_id).all()
        if categories:
            while len(form.categories) < len(categories):
                form.categories.append_entry()
            for i, category in enumerate(categories):
                form.categories[i].name.data = category.name
                
        # Load existing locations
        locations = Store.query.filter_by(company_id=current_user.company_id).all()
        if locations:
            while len(form.locations) < len(locations):
                form.locations.append_entry()
            for i, location in enumerate(locations):
                form.locations[i].name.data = location.name
    
    if form.validate_on_submit():
        try:
            # Process categories
            existing_categories = {cat.name: cat for cat in 
                                  ProductCategory.query.filter_by(company_id=current_user.company_id).all()}
            
            # Add/update categories
            for category_form in form.categories:
                if category_form.name.data:
                    if category_form.name.data in existing_categories:
                        # Category exists, no need to do anything
                        del existing_categories[category_form.name.data]
                    else:
                        # New category
                        category = ProductCategory(
                            company_id=current_user.company_id,
                            name=category_form.name.data
                        )
                        db.session.add(category)
            
            # Delete any categories that are no longer in the form
            for category in existing_categories.values():
                db.session.delete(category)
                
            # Process locations  
            existing_locations = {loc.name: loc for loc in 
                                Store.query.filter_by(company_id=current_user.company_id).all()}
            
            # Add/update locations
            for location_form in form.locations:
                if location_form.name.data:
                    if location_form.name.data in existing_locations:
                        # Location exists, no need to do anything
                        del existing_locations[location_form.name.data]
                    else:
                        # New location
                        location = Store(
                            company_id=current_user.company_id,
                            name=location_form.name.data
                        )
                        db.session.add(location)
            
            # Delete any locations that are no longer in the form
            for location in existing_locations.values():
                db.session.delete(location)
                
            db.session.commit()
            flash('Database structure updated successfully!', 'success')
            return redirect(url_for('schema.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('schema/database_setup.html', form=form)

@schema_bp.route('/data-entry/<int:category_id>', methods=['GET', 'POST'])
@login_required
@company_required
def data_entry(category_id):
    """Data entry form for a specific category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Ensure category belongs to user's company
    if category.company_id != current_user.company_id:
        flash('You do not have permission to access this category.', 'danger')
        return redirect(url_for('products.index'))
    
    form = DynamicProductForm(company_id=current_user.company_id, category_id=category_id)
    
    if form.validate_on_submit():
        try:
            # Get the dynamic fields
            dynamic_fields = form.get_dynamic_fields()
            
            # Create the product
            product = Product(
                company_id=current_user.company_id,
                name=form.name.data,
                category_id=form.category_id.data,
                base_price=form.base_price.data,
                additional_fields=dynamic_fields  # The model will handle serialization now
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('schema.data_entry', category_id=category_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # Get existing products for this category
    products = Product.query.filter_by(
        company_id=current_user.company_id,
        category_id=category_id
    ).all()
    
    return render_template('schema/data_entry.html', 
                          form=form, 
                          category=category, 
                          products=products) 