from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models.store import Store
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.sales import Sale, ProductFeature, FeatureRegistry
from app.models.company import Company
from app.forms.sales_setup_forms import (
    StoresSetupForm, CategoriesSetupForm, ProductsSetupForm, SaleEntryForm, CompanySetupForm
)
from app.utils.decorators import company_required, subscriber_required

# Create blueprint
sales_setup_bp = Blueprint('sales_setup', __name__, url_prefix='/sales/setup')

@sales_setup_bp.route('/')
@login_required
@company_required
def setup_wizard():
    """Main setup wizard that guides users through the 5-step process"""
    company_id = current_user.company_id
    
    # Check the current setup state
    company = Company.query.get(company_id)
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
    # Count products
    products_count = Product.query.filter_by(company_id=company_id).count()
    
    # Determine which step the user is on
    current_step = 1
    
    # Step 1: Company setup
    if not company or not company.name:
        current_step = 1
    # Step 2: Categories
    elif not categories:
        current_step = 2
    # Step 3: Products
    elif not products_count:
        current_step = 3
    # Step 4: Stores
    elif not stores:
        current_step = 4
    # Step 5: Complete!
    else:
        current_step = 5
        # Mark setup as complete in session
        session['setup_complete'] = True
    
    # Count completed categories with products
    categories_with_products = 0
    categories_without_products = []
    
    for category in categories:
        if Product.query.filter_by(category_id=category.id, company_id=company_id).count() > 0:
            categories_with_products += 1
        else:
            categories_without_products.append(category)
    
    return render_template(
        'sales/setup_wizard.html',
        current_step=current_step,
        company=company,
        categories_count=len(categories),
        products_count=products_count,
        stores_count=len(stores),
        categories_with_products=categories_with_products,
        categories_without_products=categories_without_products
    )

@sales_setup_bp.route('/company', methods=['GET', 'POST'])
@login_required
@company_required
def setup_company():
    """Route for setting up company details"""
    company_id = current_user.company_id
    company = Company.query.get(company_id)
    
    form = CompanySetupForm(obj=company)
    
    if form.validate_on_submit():
        # Update company details
        form.populate_obj(company)
        db.session.commit()
        flash('Company details have been successfully saved.', 'success')
        return redirect(url_for('sales_setup.setup_wizard'))
    
    return render_template('sales/setup_company.html', form=form)

@sales_setup_bp.route('/stores', methods=['GET', 'POST'])
@login_required
@company_required
def setup_stores():
    """Route for setting up stores"""
    company_id = current_user.company_id
    
    # Debug information
    print(f"Method: {request.method}")
    if request.method == 'POST':
        print(f"Form Data: {request.form}")
    
    # Check if stores already exist
    existing_stores = Store.query.filter_by(company_id=company_id).all()
    print(f"Existing stores: {len(existing_stores)}")
    
    form = StoresSetupForm()
    
    if request.method == 'GET':
        if existing_stores:
            form.num_stores.data = len(existing_stores)
            # Prepopulate the form with existing stores
            for store in existing_stores:
                store_form = {'name': store.name}
                form.stores.append_entry(store_form)
    
    # Handle form submission
    if request.method == 'POST':
        # Check if the "Update Fields" button was pressed (before form validation)
        if 'update_form' in request.form:
            print("Update Fields button pressed")
            
            # Basic validation for num_stores
            try:
                num_stores = int(request.form.get('num_stores', 0))
                if num_stores < 1:
                    flash('You must have at least one store', 'error')
                    return render_template('sales/setup_stores.html', form=form)
                    
                form.num_stores.data = num_stores
                
                # Clear existing entries and add new ones
                form.stores.entries = []
                for i in range(num_stores):
                    form.stores.append_entry({})
                    
                return render_template('sales/setup_stores.html', form=form)
            except ValueError:
                flash('Please enter a valid number of stores', 'error')
                return render_template('sales/setup_stores.html', form=form)
    
        # For the Save button, we validate the whole form
        if form.validate_on_submit():
            print(f"Form validated. Number of stores in form: {form.num_stores.data}")
            print(f"Number of store subforms: {len(form.stores)}")
            
            # Validate that all store names are provided
            all_valid = True
            for i, store_form in enumerate(form.stores):
                print(f"Store {i+1} name: '{store_form.name.data}'")
                if not store_form.name.data or not store_form.name.data.strip():
                    flash(f'Store {i+1} name cannot be empty', 'error')
                    all_valid = False
            
            if not all_valid:
                return render_template('sales/setup_stores.html', form=form)
                    
            # Delete existing stores
            if existing_stores:
                print(f"Deleting {len(existing_stores)} existing stores")
                for store in existing_stores:
                    db.session.delete(store)
                
            # Create new stores
            print("Creating new stores")
            for store_form in form.stores:
                new_store = Store(
                    name=store_form.name.data.strip(),
                    company_id=company_id
                )
                db.session.add(new_store)
            
            try:
                db.session.commit()
                print("Successfully committed store changes to database")
                flash('Stores have been successfully saved.', 'success')
                
                # Redirect to the setup wizard to continue the process
                return redirect(url_for('sales_setup.setup_wizard'))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving stores: {str(e)}")
                flash(f'Error saving stores: {str(e)}', 'error')
                return render_template('sales/setup_stores.html', form=form)
        else:
            print(f"Form validation failed. Errors: {form.errors}")
            return render_template('sales/setup_stores.html', form=form)
    
    return render_template('sales/setup_stores.html', form=form)

@sales_setup_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@company_required
def setup_categories():
    """Route for setting up product categories"""
    company_id = current_user.company_id
    
    # Debug information
    print(f"Categories Method: {request.method}")
    if request.method == 'POST':
        print(f"Categories Form Data: {request.form}")
    
    # Check if categories already exist
    existing_categories = ProductCategory.query.filter_by(company_id=company_id).all()
    print(f"Existing categories: {len(existing_categories)}")
    
    form = CategoriesSetupForm()
    
    if request.method == 'GET':
        if existing_categories:
            form.num_categories.data = len(existing_categories)
            # Prepopulate the form with existing categories
            for category in existing_categories:
                category_form = {'name': category.name}
                form.categories.append_entry(category_form)
    
    # Handle form submission
    if request.method == 'POST':
        # Check if the "Update Fields" button was pressed (before form validation)
        if 'update_form' in request.form:
            print("Update Fields button pressed for categories")
            
            # Basic validation for num_categories
            try:
                num_categories = int(request.form.get('num_categories', 0))
                if num_categories < 1:
                    flash('You must have at least one category', 'error')
                    return render_template('sales/setup_categories.html', form=form)
                    
                form.num_categories.data = num_categories
                
                # Clear existing entries and add new ones
                form.categories.entries = []
                for i in range(num_categories):
                    form.categories.append_entry({})
                    
                return render_template('sales/setup_categories.html', form=form)
            except ValueError:
                flash('Please enter a valid number of categories', 'error')
                return render_template('sales/setup_categories.html', form=form)
        
        # For the Save button, we validate the whole form
        if form.validate_on_submit():
            print(f"Categories form validated. Number of categories: {form.num_categories.data}")
            
            # Validate that all category names are provided
            all_valid = True
            for i, category_form in enumerate(form.categories):
                print(f"Category {i+1} name: '{category_form.name.data}'")
                if not category_form.name.data or not category_form.name.data.strip():
                    flash(f'Category {i+1} name cannot be empty', 'error')
                    all_valid = False
            
            if not all_valid:
                return render_template('sales/setup_categories.html', form=form)
                
            # Delete existing categories
            if existing_categories:
                print(f"Deleting {len(existing_categories)} existing categories")
                for category in existing_categories:
                    db.session.delete(category)
                
            # Create new categories
            print("Creating new categories")
            for category_form in form.categories:
                new_category = ProductCategory(
                    name=category_form.name.data.strip(),
                    company_id=company_id
                )
                db.session.add(new_category)
            
            try:
                db.session.commit()
                print("Successfully committed category changes to database")
                flash('Categories have been successfully saved.', 'success')
                return redirect(url_for('sales_setup.setup_wizard'))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving categories: {str(e)}")
                flash(f'Error saving categories: {str(e)}', 'error')
                return render_template('sales/setup_categories.html', form=form)
        else:
            print(f"Categories form validation failed. Errors: {form.errors}")
            return render_template('sales/setup_categories.html', form=form)
    
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
            return redirect(url_for('sales_setup.setup_wizard'))
    
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

@sales_setup_bp.route('/complete', methods=['GET'])
@login_required
@company_required
def setup_complete():
    """Mark setup as complete and redirect to dashboard"""
    session['setup_complete'] = True
    flash('Congratulations! Your sales database setup is complete.', 'success')
    return redirect(url_for('sales.index')) 