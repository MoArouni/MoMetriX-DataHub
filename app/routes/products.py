from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.forms.product import ProductForm, ProductCategoryForm
from app.forms.schema import DynamicProductForm
from app.models.schema import CompanySchema
from app.utils.decorators import company_required

# Create blueprint
products_bp = Blueprint('products', __name__, url_prefix='/products')

# Helper function to check if user belongs to a company
def check_company():
    """Check if user belongs to a company and redirect if not"""
    if not current_user.company_id:
        flash('You need to be part of a company to access this feature.', 'warning')
        return redirect(url_for('dashboard.index'))
    return None

@products_bp.route('/')
@login_required
@company_required
def index():
    """Show products list"""
    products = Product.query.filter_by(company_id=current_user.company_id).order_by(Product.name).all()
    categories = ProductCategory.query.filter_by(company_id=current_user.company_id).order_by(ProductCategory.name).all()
    return render_template('products/index.html', products=products, categories=categories)

@products_bp.route('/categories')
@login_required
@company_required
def categories():
    """Show categories list"""
    categories = ProductCategory.query.filter_by(company_id=current_user.company_id).order_by(ProductCategory.name).all()
    
    # Count fields per category
    for category in categories:
        category.field_count = CompanySchema.query.filter_by(
            company_id=current_user.company_id, 
            category_id=category.id
        ).count()
        
        # Count global fields that apply to all categories
        global_fields = CompanySchema.query.filter_by(
            company_id=current_user.company_id, 
            category_id=None
        ).count()
        
        category.total_fields = category.field_count + global_fields
        
    return render_template('products/categories.html', categories=categories)

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
@company_required
def new_product():
    """Create a new product"""
    # Get category ID from query parameter if provided
    category_id = request.args.get('category_id', type=int)
    
    # Check if this company has any dynamic fields set up
    has_schema = CompanySchema.query.filter_by(company_id=current_user.company_id).first() is not None
    
    if has_schema and category_id:
        # Use dynamic form if schema exists and category is selected
        return redirect(url_for('schema.data_entry', category_id=category_id))
    elif has_schema:
        # If schema exists but no category selected, show category selection
        categories = ProductCategory.query.filter_by(company_id=current_user.company_id).order_by(ProductCategory.name).all()
        return render_template('products/category_select.html', categories=categories)
    else:
        # Use regular form if no schema exists
        form = ProductForm(company_id=current_user.company_id)
        
        if form.validate_on_submit():
            product = Product(
                company_id=current_user.company_id,
                name=form.name.data,
                category_id=form.category_id.data,
                base_price=form.base_price.data,
                active=form.active.data
            )
            db.session.add(product)
            db.session.commit()
            flash('Product created successfully!', 'success')
            return redirect(url_for('products.index'))
            
        return render_template('products/form.html', form=form, title='New Product')

@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.get_or_404(product_id)
    
    # Ensure product belongs to user's company
    if product.company_id != current_user.company_id:
        flash('You do not have permission to edit this product.', 'danger')
        return redirect(url_for('products.index'))
    
    # Check if this company has any dynamic fields set up
    has_schema = CompanySchema.query.filter_by(company_id=current_user.company_id).first() is not None
    
    if has_schema and product.additional_fields:
        # Use dynamic form with pre-filled values if schema exists and product has additional fields
        flash('This product uses dynamic fields. Edit from the data entry form.', 'info')
        return redirect(url_for('schema.data_entry', category_id=product.category_id))
    else:
        # Use regular form
        form = ProductForm(company_id=current_user.company_id, obj=product)
        
        if form.validate_on_submit():
            form.populate_obj(product)
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products.index'))
            
        return render_template('products/form.html', form=form, title='Edit Product', product=product)

@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
@company_required
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    
    # Ensure product belongs to user's company
    if product.company_id != current_user.company_id:
        flash('You do not have permission to delete this product.', 'danger')
        return redirect(url_for('products.index'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products.index'))

@products_bp.route('/category/new', methods=['GET', 'POST'])
@login_required
@company_required
def new_category():
    """Create a new category"""
    form = ProductCategoryForm()
    
    if form.validate_on_submit():
        category = ProductCategory(
            company_id=current_user.company_id,
            name=form.name.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('products.categories'))
        
    return render_template('products/category_form.html', form=form, title='New Category')

@products_bp.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_category(category_id):
    """Edit an existing category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Ensure category belongs to user's company
    if category.company_id != current_user.company_id:
        flash('You do not have permission to edit this category.', 'danger')
        return redirect(url_for('products.categories'))
    
    form = ProductCategoryForm(obj=category)
    
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('products.categories'))
        
    return render_template('products/category_form.html', form=form, title='Edit Category', category=category)

@products_bp.route('/category/delete/<int:category_id>', methods=['POST'])
@login_required
@company_required
def delete_category(category_id):
    """Delete a category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Ensure category belongs to user's company
    if category.company_id != current_user.company_id:
        flash('You do not have permission to delete this category.', 'danger')
        return redirect(url_for('products.categories'))
    
    # Check if there are products in this category
    products_count = Product.query.filter_by(category_id=category_id).count()
    if products_count > 0:
        flash(f'Cannot delete category: There are {products_count} products assigned to it.', 'warning')
        return redirect(url_for('products.categories'))
    
    # Check if there are schema fields for this category
    schema_count = CompanySchema.query.filter_by(category_id=category_id).count()
    if schema_count > 0:
        flash(f'Cannot delete category: There are {schema_count} schema fields assigned to it.', 'warning')
        return redirect(url_for('products.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('products.categories'))

@products_bp.route('/category/<int:category_id>/fields')
@login_required
@company_required
def category_fields(category_id):
    """Show fields for a specific category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Ensure category belongs to user's company
    if category.company_id != current_user.company_id:
        flash('You do not have permission to view this category.', 'danger')
        return redirect(url_for('products.categories'))
    
    # Get fields specific to this category
    category_fields = CompanySchema.query.filter_by(
        company_id=current_user.company_id,
        category_id=category_id
    ).order_by(CompanySchema.display_order, CompanySchema.field_name).all()
    
    # Get global fields
    global_fields = CompanySchema.query.filter_by(
        company_id=current_user.company_id,
        category_id=None
    ).order_by(CompanySchema.display_order, CompanySchema.field_name).all()
    
    return render_template('products/category_fields.html', 
                          category=category, 
                          category_fields=category_fields,
                          global_fields=global_fields)

@products_bp.route('/category/<int:category_id>/products')
@login_required
@company_required
def category_products(category_id):
    """Show products for a specific category"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Ensure category belongs to user's company
    if category.company_id != current_user.company_id:
        flash('You do not have permission to view this category.', 'danger')
        return redirect(url_for('products.categories'))
    
    products = Product.query.filter_by(
        company_id=current_user.company_id,
        category_id=category_id
    ).order_by(Product.name).all()
    
    return render_template('products/category_products.html', 
                          category=category, 
                          products=products)

# API endpoint to get product details (for AJAX)
@products_bp.route('/api/product/<int:product_id>')
@login_required
@company_required
def api_product_details(product_id):
    """Get product details as JSON"""
    product = Product.query.get_or_404(product_id)
    
    # Ensure product belongs to user's company
    if product.company_id != current_user.company_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    result = {
        'product_id': product.product_id,
        'name': product.name,
        'base_price': float(product.base_price),
        'category_id': product.category_id,
        'active': product.active
    }
    
    # Add additional fields if they exist
    if product.additional_fields:
        result['additional_fields'] = product.additional_fields
    
    return jsonify(result)

@products_bp.route('/select-category')
@login_required
@company_required
def select_category():
    """Select a category before adding a product"""
    categories = ProductCategory.query.filter_by(company_id=current_user.company_id).order_by(ProductCategory.name).all()
    return render_template('products/category_select.html', categories=categories)

@products_bp.route('/view/<int:product_id>')
@login_required
@company_required
def view_product(product_id):
    """View a product's details"""
    product = Product.query.get_or_404(product_id)
    
    # Ensure product belongs to user's company
    if product.company_id != current_user.company_id:
        flash('You do not have permission to view this product.', 'danger')
        return redirect(url_for('products.index'))
    
    # Get custom fields if they exist
    custom_fields = None
    if product.additional_fields:
        custom_fields = product.additional_fields
        
        # Get field definitions for better display
        if custom_fields:
            field_defs = {}
            schema_fields = CompanySchema.query.filter(
                (CompanySchema.company_id == current_user.company_id) & 
                ((CompanySchema.category_id == product.category_id) | (CompanySchema.category_id == None))
            ).all()
            
            for field in schema_fields:
                field_defs[field.field_name] = {
                    'type': field.field_type,
                    'label': field.field_name.replace('_', ' ').title()
                }
            
            # Add the definitions to the custom fields
            for field_name, value in custom_fields.items():
                if field_name in field_defs:
                    custom_fields[field_name] = {
                        'value': value,
                        'type': field_defs[field_name]['type'],
                        'label': field_defs[field_name]['label']
                    }
    
    return render_template('products/view.html', product=product, custom_fields=custom_fields) 