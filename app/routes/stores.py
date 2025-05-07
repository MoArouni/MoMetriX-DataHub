from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.store import Store
from app.forms.sales_setup_forms import StoresSetupForm
from app.utils.decorators import company_required
from app.models.subscription import CompanySubscription

# Create blueprint
stores_bp = Blueprint('stores', __name__, url_prefix='/stores')

@stores_bp.route('/')
@login_required
@company_required
def index():
    """Show stores list"""
    try:
        stores = Store.query.filter_by(company_id=current_user.company_id).order_by(Store.name).all()
        return render_template('stores/index.html', stores=stores)
    except Exception as e:
        # Log the error
        print(f"Error in stores.index: {str(e)}")
        flash('An error occurred while loading stores. Please try again.', 'error')
        return redirect(url_for('dashboard.dashboard'))

@stores_bp.route('/manage', methods=['GET', 'POST'])
@login_required
@company_required
def manage():
    """Manage company stores"""
    try:
        company_id = current_user.company_id
        
        # Check subscription limits
        subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
        max_stores = 3  # Default free plan limit
        
        # Check if stores already exist
        existing_stores = Store.query.filter_by(company_id=company_id).all()
        
        form = StoresSetupForm()
        
        if request.method == 'GET':
            if existing_stores:
                form.num_stores.data = len(existing_stores)
                # Prepopulate the form with existing stores
                form.stores.entries = []  # Clear existing entries first
                for store in existing_stores:
                    store_form = {'name': store.name, 'location': store.location or ''}
                    form.stores.append_entry(store_form)
            else:
                # Default to one store
                form.num_stores.data = 1
                form.stores.append_entry({})
        
        # Handle form submission
        if request.method == 'POST':
            # Check if the "Update Fields" button was pressed (before form validation)
            if 'update_form' in request.form:
                # Basic validation for num_stores
                try:
                    num_stores = int(request.form.get('num_stores', 0))
                    
                    # Check if number of stores exceeds the limit
                    if num_stores > max_stores:
                        flash(f'Free plan is limited to {max_stores} stores. Please upgrade your plan for more.', 'warning')
                        return redirect(url_for('pricing.index'))
                        
                    if num_stores < 1:
                        num_stores = 1
                        flash('You must have at least one store.', 'warning')
                        
                    form.num_stores.data = num_stores
                    
                    # Clear existing entries and add new ones
                    form.stores.entries = []
                    for i in range(num_stores):
                        form.stores.append_entry({})
                        
                    return render_template('stores/manage.html', form=form, max_stores=max_stores)
                except (ValueError, TypeError) as e:
                    flash('Please enter a valid number of stores.', 'error')
                    # Reset form to default state
                    form.num_stores.data = len(existing_stores) if existing_stores else 1
                    form.stores.entries = []
                    for store in existing_stores:
                        store_form = {'name': store.name, 'location': store.location or ''}
                        form.stores.append_entry(store_form)
                    return render_template('stores/manage.html', form=form, max_stores=max_stores)
            
            # Check if the "Save Stores" button was pressed
            elif 'submit' in request.form:
                try:
                    # Check if number of stores exceeds the limit
                    if form.num_stores.data > max_stores:
                        flash(f'Free plan is limited to {max_stores} stores. Please upgrade your plan for more.', 'warning')
                        return redirect(url_for('pricing.index'))
                        
                    # Validate that all store names are provided
                    all_valid = True
                    for i, store_form in enumerate(form.stores):
                        if not store_form.name.data or not store_form.name.data.strip():
                            flash(f'Store {i+1} name cannot be empty', 'error')
                            all_valid = False
                    
                    if not all_valid:
                        return render_template('stores/manage.html', form=form, max_stores=max_stores)
                        
                    # Delete existing stores
                    if existing_stores:
                        for store in existing_stores:
                            db.session.delete(store)
                        
                    # Create new stores
                    for store_form in form.stores:
                        if store_form.name.data and store_form.name.data.strip():
                            new_store = Store(
                                name=store_form.name.data.strip(),
                                location=store_form.location.data.strip() if store_form.location.data else '',
                                company_id=company_id
                            )
                            db.session.add(new_store)
                    
                    db.session.commit()
                    flash('Stores have been successfully saved.', 'success')
                    return redirect(url_for('stores.index'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error saving stores: {str(e)}', 'error')
                    return render_template('stores/manage.html', form=form, max_stores=max_stores)
        
        return render_template('stores/manage.html', form=form, max_stores=max_stores)
    except Exception as e:
        # Log the error
        print(f"Error in stores.manage: {str(e)}")
        flash('An error occurred while managing stores. Please try again.', 'error')
        return redirect(url_for('dashboard.dashboard')) 