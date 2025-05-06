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
from app.forms.company import CompanyForm
from app.utils.decorators import company_required, subscriber_required
import json

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
    if not company or not company.company_name:
        current_step = 1
        # Redirect to company setup if viewing the wizard
        if request.args.get('redirect', 'false') == 'true':
            return redirect(url_for('sales_setup.setup_company'))
    # Step 2: Categories
    elif not categories:
        current_step = 2
        # Redirect to categories setup if viewing the wizard
        if request.args.get('redirect', 'false') == 'true':
            return redirect(url_for('sales_setup.setup_categories'))
    # Step 3: Products
    elif not products_count:
        current_step = 3
        # Redirect to products setup if viewing the wizard
        if request.args.get('redirect', 'false') == 'true':
            return redirect(url_for('sales_setup.setup_products'))
    # Step 4: Stores
    elif not stores:
        current_step = 4
        # Redirect to stores setup if viewing the wizard
        if request.args.get('redirect', 'false') == 'true':
            return redirect(url_for('sales_setup.setup_stores'))
    # Step 5: Complete!
    else:
        current_step = 5
        # Mark setup as complete in session
        session['setup_complete'] = True
        
        # Redirect to completion page if viewing the wizard
        if request.args.get('redirect', 'false') == 'true':
            return redirect(url_for('sales_setup.setup_complete'))
    
    # Check if the user is asking to go to the current step
    if request.args.get('goto_current', 'false') == 'true':
        if current_step == 1:
            return redirect(url_for('sales_setup.setup_company'))
        elif current_step == 2:
            return redirect(url_for('sales_setup.setup_categories'))
        elif current_step == 3:
            return redirect(url_for('sales_setup.setup_products'))
        elif current_step == 4:
            return redirect(url_for('sales_setup.setup_stores'))
        elif current_step == 5:
            return redirect(url_for('sales_setup.setup_complete'))
    
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
        categories_count=len(categories) if categories else 0,
        products_count=products_count,
        stores_count=len(stores) if stores else 0,
        categories_with_products=categories_with_products,
        categories_without_products=categories_without_products
    )

@sales_setup_bp.route('/company', methods=['GET', 'POST'])
@login_required
def setup_company():
    """Route for setting up company details"""
    # Check if user already has a company
    if current_user.company_id:
        company = Company.query.get(current_user.company_id)
    else:
        company = None
    
    form = CompanySetupForm()
    
    # Pre-populate the form with existing company data if it exists
    if request.method == 'GET' and company:
        form.company_name.data = company.company_name
        form.company_email.data = company.company_email
        form.phone.data = company.phone
    
    if form.validate_on_submit():
        if company:
            # Update existing company
            company.company_name = form.company_name.data
            company.company_email = form.company_email.data
            company.phone = form.phone.data
        else:
            # Create new company
            company = Company(
                company_name=form.company_name.data,
                company_email=form.company_email.data,
                phone=form.phone.data
            )
            db.session.add(company)
            db.session.flush()  # Get the company ID
            
            # Associate the company with the user
            current_user.company_id = company.id
        
        db.session.commit()
        flash('Company details have been successfully saved.', 'success')
        
        # Mark the setup step as completed
        session['company_setup_completed'] = True
        
        # Redirect to the next setup step
        return redirect(url_for('sales_setup.setup_categories'))
    
    return render_template('sales/setup_company.html', form=form)

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
    
    # Handle the update_form button click
    if 'update_form' in request.form:
        num_stores = int(request.form.get('num_stores', 0))
        form.num_stores.data = num_stores
        
        # Adjust the form fields
        while len(form.stores) < num_stores:
            form.stores.append_entry({})
        while len(form.stores) > num_stores:
            form.stores.pop_entry()
            
        return render_template('sales/setup_stores.html', form=form)
    
    if form.validate_on_submit() and 'submit' in request.form:
        # Delete existing stores
        if existing_stores:
            for store in existing_stores:
                db.session.delete(store)
        
        # Create new stores
        for i in range(form.num_stores.data):
            store_name = request.form.get(f'stores-{i}-name')
            if store_name:
                new_store = Store(
                    name=store_name,
                    company_id=company_id
                )
                db.session.add(new_store)
        
        db.session.commit()
        flash('Stores have been successfully saved.', 'success')
        
        # Mark the setup step as completed
        session['stores_setup_completed'] = True
        
        # All required setup steps are now completed
        session['setup_complete'] = True
        
        # Redirect to setup complete page
        return redirect(url_for('sales_setup.setup_complete'))
    
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
    
    # Handle the Update Form button click
    if 'Update Form' in request.form.values():
        try:
            num_products = int(request.form.get('num_products', 0))
            if num_products < 1:
                flash('You must have at least one product', 'error')
                return render_template('sales/setup_products.html', form=form, category=category)
                
            form.num_products.data = num_products
            
            # Clear existing entries and add new ones
            form.products.entries = []
            for i in range(num_products):
                form.products.append_entry({})
                
            return render_template('sales/setup_products.html', form=form, category=category)
        except ValueError:
            flash('Please enter a valid number of products', 'error')
            return render_template('sales/setup_products.html', form=form, category=category)
    
    if form.validate_on_submit() and 'submit' in request.form:
        # Delete existing products
        if existing_products:
            for product in existing_products:
                db.session.delete(product)
        
        # Create new products from form data
        for i in range(form.num_products.data):
            product_name = request.form.get(f'products-{i}-name')
            if product_name and product_name.strip():
                new_product = Product(
                    name=product_name.strip(),
                    category_id=category_id,
                    company_id=company_id,
                    additional_fields=json.dumps({})  # Properly serialized empty JSON object
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
            # Mark the products setup as completed
            session['products_setup_completed'] = True
            # Redirect to the next step - stores
            return redirect(url_for('sales_setup.setup_stores'))
    
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

@sales_setup_bp.route('/mods', methods=['GET', 'POST'])
@login_required
@company_required
def setup_mods():
    """Route for setting up optional modifications/features"""
    # This could be expanded to include custom fields or options
    
    if request.method == 'POST':
        # Process and save any mods
        
        # Mark the setup step as completed
        session['mods_setup_completed'] = True
        
        # Redirect to the next step
        return redirect(url_for('sales_setup.setup_payment'))
    
    # If skipping this step
    if request.args.get('skip'):
        session['mods_skipped'] = True
        return redirect(url_for('sales_setup.setup_payment'))
    
    return render_template('sales/setup_mods.html')

@sales_setup_bp.route('/payment', methods=['GET', 'POST'])
@login_required
@company_required
def setup_payment():
    """Route for setting up payment options"""
    # This would be for integrating payment processing
    
    if request.method == 'POST':
        # Process and save payment info
        
        # Mark the setup step as completed
        session['payment_setup_completed'] = True
        
        # Redirect to completion
        return redirect(url_for('sales_setup.setup_complete'))
    
    # If skipping this step
    if request.args.get('skip'):
        session['payment_skipped'] = True
        return redirect(url_for('sales_setup.setup_complete'))
    
    return render_template('sales/setup_payment.html')

@sales_setup_bp.route('/complete')
@login_required
@company_required
def setup_complete():
    """Route for setup completion"""
    company_id = current_user.company_id
    
    # Check if all required steps are completed
    company = Company.query.get(current_user.company_id)
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    products_count = Product.query.filter_by(company_id=company_id).count()
    
    # If any required steps are incomplete, redirect to the wizard to continue setup
    if not company or not company.company_name or not categories or not products_count or not stores:
        flash('Please complete all setup steps before proceeding.', 'warning')
        return redirect(url_for('sales_setup.setup_wizard'))
    
    # Mark setup as fully completed
    session['setup_completed'] = True
    
    # Get summary information for the completion page
    company_name = company.company_name if company else "Your Company"
    categories_count = len(categories)
    stores_count = len(stores)
    
    flash('Setup complete! You can now start using your sales database.', 'success')
    return render_template('sales/setup_complete.html', 
                          company_name=company_name,
                          categories_count=categories_count,
                          products_count=products_count,
                          stores_count=stores_count)