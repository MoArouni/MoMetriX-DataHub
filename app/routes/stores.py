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
        print("DEBUG: Starting stores.manage function")
        company_id = current_user.company_id
        print(f"DEBUG: Company ID: {company_id}")
        
        # Check subscription limits
        subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
        max_stores = 3  # Default free plan limit
        print(f"DEBUG: Max stores: {max_stores}")
        
        # Check if stores already exist
        existing_stores = Store.query.filter_by(company_id=company_id).all()
        print(f"DEBUG: Found {len(existing_stores)} existing stores")
        
        print("DEBUG: Creating StoresSetupForm")
        form = StoresSetupForm()
        print("DEBUG: Form created successfully")
        
        # Test form field access
        print("DEBUG: Testing form field access")
        try:
            print(f"DEBUG: form.stores type: {type(form.stores)}")
            print(f"DEBUG: form.stores.entries type: {type(form.stores.entries)}")
            print(f"DEBUG: form.stores.entries length: {len(form.stores.entries)}")
        except Exception as e:
            print(f"DEBUG: Error accessing form.stores: {e}")
            import traceback
            traceback.print_exc()
        
        if request.method == 'GET':
            print("DEBUG: Processing GET request")
            if existing_stores:
                print("DEBUG: Prepopulating form with existing stores")
                form.num_stores.data = len(existing_stores)
                # Prepopulate the form with existing stores
                form.stores.entries = []  # Clear existing entries first
                for i, store in enumerate(existing_stores):
                    print(f"DEBUG: Processing store {i}: {store.name}")
                    try:
                        print(f"DEBUG: About to call append_entry()")
                        form.stores.append_entry()
                        print(f"DEBUG: Entry appended successfully")
                        print(f"DEBUG: form.stores.entries length now: {len(form.stores.entries)}")
                        print(f"DEBUG: Last entry type: {type(form.stores[-1])}")
                        print(f"DEBUG: Last entry has store_name: {hasattr(form.stores[-1], 'store_name')}")
                        print(f"DEBUG: Last entry has location: {hasattr(form.stores[-1], 'location')}")
                        
                        # Set the data after creating the entry
                        print(f"DEBUG: Setting name data: {store.name}")
                        form.stores[-1].store_name.data = store.name
                        print(f"DEBUG: Setting location data: {store.location or ''}")
                        form.stores[-1].location.data = store.location or ''
                        print(f"DEBUG: Data set for store {i}")
                    except Exception as e:
                        print(f"DEBUG: Error processing store {i}: {e}")
                        import traceback
                        traceback.print_exc()
                        raise
            else:
                print("DEBUG: No existing stores, creating default entry")
                # Default to one store
                form.num_stores.data = 1
                try:
                    print("DEBUG: About to call append_entry() for default")
                    form.stores.append_entry()
                    print("DEBUG: Default entry created successfully")
                    print(f"DEBUG: form.stores.entries length: {len(form.stores.entries)}")
                    
                    # Debug the created entry
                    if len(form.stores.entries) > 0:
                        entry = form.stores.entries[0]
                        print(f"DEBUG: Entry type: {type(entry)}")
                        print(f"DEBUG: Entry dir: {dir(entry)}")
                        if hasattr(entry, 'store_name'):
                            print(f"DEBUG: Entry.store_name type: {type(entry.store_name)}")
                            print(f"DEBUG: Entry.store_name value: {entry.store_name}")
                        if hasattr(entry, 'location'):
                            print(f"DEBUG: Entry.location type: {type(entry.location)}")
                            print(f"DEBUG: Entry.location value: {entry.location}")
                except Exception as e:
                    print(f"DEBUG: Error creating default entry: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
        
        # Handle form submission
        if request.method == 'POST':
            print("DEBUG: Processing POST request")
            # Check if the "Update Fields" button was pressed (before form validation)
            if 'update_form' in request.form:
                print("DEBUG: Update form button pressed")
                # Basic validation for num_stores
                try:
                    num_stores = int(request.form.get('num_stores', 0))
                    print(f"DEBUG: Requested num_stores: {num_stores}")
                    
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
                        print(f"DEBUG: Adding entry {i}")
                        form.stores.append_entry()
                        
                    return render_template('stores/manage.html', form=form, max_stores=max_stores)
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error in update_form: {e}")
                    flash('Please enter a valid number of stores.', 'error')
                    # Reset form to default state
                    form.num_stores.data = len(existing_stores) if existing_stores else 1
                    form.stores.entries = []
                    for store in existing_stores:
                        form.stores.append_entry()
                        # Set the data after creating the entry
                        form.stores[-1].store_name.data = store.name
                        form.stores[-1].location.data = store.location or ''
                    return render_template('stores/manage.html', form=form, max_stores=max_stores)
            
            # Check if the "Save Stores" button was pressed
            elif 'submit' in request.form:
                print("DEBUG: Submit button pressed")
                try:
                    # Check if number of stores exceeds the limit
                    if form.num_stores.data > max_stores:
                        flash(f'Free plan is limited to {max_stores} stores. Please upgrade your plan for more.', 'warning')
                        return redirect(url_for('pricing.index'))
                        
                    # Validate that all store names are provided
                    all_valid = True
                    for i, store_form in enumerate(form.stores):
                        if not store_form.store_name.data or not store_form.store_name.data.strip():
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
                        if store_form.store_name.data and store_form.store_name.data.strip():
                            new_store = Store(
                                name=store_form.store_name.data.strip(),
                                location=store_form.location.data.strip() if store_form.location.data else '',
                                company_id=company_id
                            )
                            db.session.add(new_store)
                    
                    db.session.commit()
                    flash('Stores have been successfully saved.', 'success')
                    return redirect(url_for('stores.index'))
                except Exception as e:
                    print(f"DEBUG: Error in submit: {e}")
                    db.session.rollback()
                    flash(f'Error saving stores: {str(e)}', 'error')
                    return render_template('stores/manage.html', form=form, max_stores=max_stores)
        
        print("DEBUG: Rendering template")
        return render_template('stores/manage.html', form=form, max_stores=max_stores)
    except Exception as e:
        # Log the error
        print(f"Error in stores.manage: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while managing stores. Please try again.', 'error')
        return redirect(url_for('dashboard.dashboard')) 