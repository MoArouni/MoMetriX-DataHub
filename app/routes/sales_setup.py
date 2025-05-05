from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.store import Store
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.sales import Sale, ProductFeature, FeatureRegistry
from app.forms.sales_setup_forms import (
    StoresSetupForm, CategoriesSetupForm, ProductsSetupForm, SaleEntryForm
)
from app.utils.decorators import company_required, subscriber_required

# Create blueprint
sales_setup_bp = Blueprint('sales_setup', __name__, url_prefix='/sales/setup')

@sales_setup_bp.route('/stores', methods=['GET', 'POST'])
@login_required
@company_required
def setup_stores():
    """Route for setting up stores"""
    company_id = current_user.company_id
    
    # Check if stores already exist
    existing_stores = Store.query.filter_by(company_id=company_id).all()
    
    form = StoresSetupForm()
    
    if request.method == 'GET':
        if existing_stores:
            form.num_stores.data = len(existing_stores)
            # Prepopulate the form with existing stores
            for store in existing_stores:
                store_form = {'name': store.name}
                form.stores.append_entry(store_form)
    
    if form.validate_on_submit():
        # If number of stores has changed, adjust the form
        if len(form.stores) != form.num_stores.data:
            while len(form.stores) < form.num_stores.data:
                form.stores.append_entry({})
            while len(form.stores) > form.num_stores.data:
                form.stores.pop_entry()
            return render_template('sales/setup_stores.html', form=form)
        
        # Delete existing stores
        if existing_stores:
            for store in existing_stores:
                db.session.delete(store)
            
        # Create new stores
        for store_form in form.stores:
            new_store = Store(
                name=store_form.name.data,
                company_id=company_id
            )
            db.session.add(new_store)
        
        db.session.commit()
        flash('Stores have been successfully saved.', 'success')
        
        # Check if categories exist, if not, redirect to category setup
        categories = ProductCategory.query.filter_by(company_id=company_id).all()
        if not categories:
            return redirect(url_for('sales_setup.setup_categories'))
        else:
            return redirect(url_for('sales.index'))
    
    return render_template('sales/setup_stores.html', form=form)

@sales_setup_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@company_required
def setup_categories():
    """Route for setting up product categories"""
    company_id = current_user.company_id
    
    # Check if categories already exist
    existing_categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
    form = CategoriesSetupForm()
    
    if request.method == 'GET':
        if existing_categories:
            form.num_categories.data = len(existing_categories)
            # Prepopulate the form with existing categories
            for category in existing_categories:
                category_form = {'name': category.name}
                form.categories.append_entry(category_form)
    
    if form.validate_on_submit():
        # If number of categories has changed, adjust the form
        if len(form.categories) != form.num_categories.data:
            while len(form.categories) < form.num_categories.data:
                form.categories.append_entry({})
            while len(form.categories) > form.num_categories.data:
                form.categories.pop_entry()
            return render_template('sales/setup_categories.html', form=form)
        
        # Delete existing categories
        if existing_categories:
            for category in existing_categories:
                db.session.delete(category)
            
        # Create new categories
        for category_form in form.categories:
            new_category = ProductCategory(
                name=category_form.name.data,
                company_id=company_id
            )
            db.session.add(new_category)
        
        db.session.commit()
        flash('Categories have been successfully saved.', 'success')
        return redirect(url_for('sales_setup.setup_products'))
    
    return render_template('sales/setup_categories.html', form=form)

@sales_setup_bp.route('/products', methods=['GET'])
@login_required
@company_required
def setup_products():
    """Route for product setup selection"""
    company_id = current_user.company_id
    
    # Get all categories
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
    if not categories:
        flash('Please set up categories first.', 'warning')
        return redirect(url_for('sales_setup.setup_categories'))
    
    return render_template('sales/select_category.html', categories=categories)

@sales_setup_bp.route('/products/<int:category_id>', methods=['GET', 'POST'])
@login_required
@company_required
def setup_category_products(category_id):
    """Route for setting up products within a category"""
    company_id = current_user.company_id
    
    # Verify category exists and belongs to the company
    category = ProductCategory.query.filter_by(id=category_id, company_id=company_id).first_or_404()
    
    # Check if products already exist for this category
    existing_products = Product.query.filter_by(category_id=category_id, company_id=company_id).all()
    
    form = ProductsSetupForm()
    form.category_id.data = category_id
    
    if request.method == 'GET':
        if existing_products:
            form.num_products.data = len(existing_products)
            # Prepopulate the form with existing products
            for product in existing_products:
                product_form = {'name': product.name}
                form.products.append_entry(product_form)
    
    if form.validate_on_submit():
        # If number of products has changed, adjust the form
        if len(form.products) != form.num_products.data:
            while len(form.products) < form.num_products.data:
                form.products.append_entry({})
            while len(form.products) > form.num_products.data:
                form.products.pop_entry()
            return render_template('sales/setup_products.html', form=form, category=category)
        
        # Delete existing products
        if existing_products:
            for product in existing_products:
                db.session.delete(product)
            
        # Create new products
        for product_form in form.products:
            new_product = Product(
                name=product_form.name.data,
                category_id=category_id,
                company_id=company_id
            )
            db.session.add(new_product)
        
        db.session.commit()
        flash(f'Products for {category.name} have been successfully saved.', 'success')
        
        # Check if there are more categories to set up
        remaining_categories = ProductCategory.query.filter(
            ProductCategory.company_id == company_id,
            ProductCategory.id != category_id,
            ~ProductCategory.products.any()
        ).first()
        
        if remaining_categories:
            return redirect(url_for('sales_setup.setup_products'))
        else:
            flash('All categories now have products! Your sales database is ready to use.', 'success')
            return redirect(url_for('sales.index'))
    
    return render_template('sales/setup_products.html', form=form, category=category)

@sales_setup_bp.route('/api/feature-registry', methods=['GET'])
@login_required
@company_required
def feature_registry_api():
    """API endpoint for feature registry autocomplete"""
    company_id = current_user.company_id
    feature_name = request.args.get('name', '')
    
    features = FeatureRegistry.query.filter(
        FeatureRegistry.company_id == company_id,
        FeatureRegistry.name.ilike(f'{feature_name}%')
    ).order_by(FeatureRegistry.usage_count.desc()).limit(10).all()
    
    result = [{'name': f.name, 'value': f.value, 'usage_count': f.usage_count} for f in features]
    return jsonify(result)

@sales_setup_bp.route('/api/feature-values', methods=['GET'])
@login_required
@company_required
def feature_values_api():
    """API endpoint for feature values autocomplete"""
    company_id = current_user.company_id
    feature_name = request.args.get('name', '')
    
    features = FeatureRegistry.query.filter(
        FeatureRegistry.company_id == company_id,
        FeatureRegistry.name == feature_name
    ).order_by(FeatureRegistry.usage_count.desc()).limit(10).all()
    
    result = [{'value': f.value, 'usage_count': f.usage_count} for f in features]
    return jsonify(result) 