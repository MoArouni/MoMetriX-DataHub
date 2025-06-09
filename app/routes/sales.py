from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, make_response, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_
from app import db
from app.models.store import Store
from app.models.product import Product, Embellishment
from app.models.product_category import ProductCategory
from app.models.sales import Sale
from app.models.roles import RoleCompany
from app.forms.sales_setup_forms import SaleEntryForm
from app.utils.decorators import company_required, subscriber_required
from app.models.subscription import CompanySubscription
from app.services.sales_import_export import SalesImportExportService
from datetime import datetime, date
import json
import io
import tempfile
import os
import uuid

# Create blueprint
sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
@login_required
@company_required
def index():
    """Sales dashboard"""
    company_id = current_user.company_id
    
    # Check if user is admin (role_company is stored directly in User model)
    is_admin = current_user.role_company == 'admin'
    
    # Check if company has stores, categories, and products set up
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
    # Get all products for filter
    products = Product.query.filter_by(company_id=company_id).all()
    
    # Check subscription status and limits
    subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
    near_limit = False
    hit_limit = False
    
    if subscription:
        if subscription.sales_usage_percent >= 80 and subscription.sales_usage_percent < 100:
            near_limit = True
        elif subscription.sales_usage_percent >= 100:
            hit_limit = True
    
    # Check if session has a forced setup complete flag
    if session.get('setup_complete', False):
        setup_complete = True
        missing_setup = []
    else:
        # Check if any categories have products
        has_products = False
        if categories:
            for category in categories:
                product_count = Product.query.filter_by(company_id=company_id, category_id=category.id).count()
                if product_count > 0:
                    has_products = True
                    break
        
        # Setup is complete if there are stores, categories, and at least one product
        setup_complete = bool(stores and categories and has_products)
        
        # If setup is not complete, determine what's missing
        missing_setup = []
        if not stores:
            missing_setup.append('stores')
        if not categories:
            missing_setup.append('product categories')
        if not has_products and categories:
            missing_setup.append('products for your categories')
    
    # Get recent sales
    recent_sales = Sale.query.filter_by(company_id=company_id).order_by(desc(Sale.created_at)).limit(10).all()
    
    # Calculate daily sales total
    today = date.today()
    daily_sales = db.session.query(func.sum(Sale.card_amount + Sale.cash_amount)).filter(
        Sale.company_id == company_id,
        func.date(Sale.created_at) == today
    ).scalar() or 0
    
    # Calculate monthly sales total
    monthly_sales = db.session.query(func.sum(Sale.card_amount + Sale.cash_amount)).filter(
        Sale.company_id == company_id,
        func.extract('month', Sale.created_at) == today.month,
        func.extract('year', Sale.created_at) == today.year
    ).scalar() or 0
    
    return render_template(
        'sales/index.html',
        setup_complete=setup_complete,
        missing_setup=missing_setup,
        recent_sales=recent_sales,
        daily_sales=daily_sales,
        monthly_sales=monthly_sales,
        store_count=len(stores),
        category_count=len(categories),
        stores=stores,
        products=products,
        near_limit=near_limit,
        hit_limit=hit_limit,
        subscription=subscription,
        is_admin=is_admin
    )

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
@company_required
def new_sale():
    """Create a new sale entry"""
    company_id = current_user.company_id
    
    # Check subscription limits
    subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
    if subscription and not subscription.can_add_sale:
        flash('You have reached the maximum number of sales allowed under your current plan. Please upgrade to add more sales.', 'warning')
        return redirect(url_for('pricing.index'))
    
    # Check if company has necessary setup
    stores = Store.query.filter_by(company_id=company_id).all()
    if not stores:
        flash('You need to create at least one store before recording sales.', 'warning')
        return redirect(url_for('stores.manage'))
    
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    if not categories:
        flash('You need to create at least one product category before recording sales.', 'warning')
        return redirect(url_for('products.categories'))
    
    # Check if there are products in any category
    has_products = False
    for category in categories:
        product_count = Product.query.filter_by(company_id=company_id, category_id=category.id).count()
        if product_count > 0:
            has_products = True
            break
    
    if not has_products:
        flash('You need to add products to at least one category before recording sales.', 'warning')
        return redirect(url_for('products.new_product'))
    
    form = SaleEntryForm()
    
    # Populate dropdown choices
    form.store_id.choices = [(store.id, store.name) for store in stores]
    
    # Get product choices grouped by category
    product_choices_by_category = {}
    for category in categories:
        category_products = Product.query.filter_by(company_id=company_id, category_id=category.id).all()
        if category_products:  # Only add categories that have products
            product_choices_by_category[category.id] = {
                'name': category.name,
                'products': [(product.id, product.name) for product in category_products]
            }
    
    # If we have no categories with products despite having products, redirect
    if not product_choices_by_category:
        flash('There are no active products available. Please add products before recording a sale.', 'warning')
        return redirect(url_for('products.new_product'))
    
    if form.validate_on_submit():
        # Validate payment amounts
        total_amount = form.cash_amount.data + form.card_amount.data
        if total_amount <= 0:
            flash('Total payment amount must be greater than zero.', 'error')
            return render_template(
                'sales/new_sale.html',
                form=form,
                stores=stores,
                product_choices=product_choices_by_category
            )
        
        # Create new sale
        new_sale = Sale(
            company_id=company_id,
            user_id=current_user.id,
            store_id=form.store_id.data,
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            cash_amount=form.cash_amount.data,
            card_amount=form.card_amount.data,
            notes=form.notes.data if form.notes.data else None,
            sale_date=date.today()
        )
        db.session.add(new_sale)
        db.session.flush()  # Get the sale ID without committing
        
        # Process embellishments
        embellishment_ids = request.form.getlist('embellishment_ids')
        if embellishment_ids:
            for emb_id in embellishment_ids:
                try:
                    embellishment = Embellishment.query.get(int(emb_id))
                    if embellishment and embellishment.company_id == company_id:
                        new_sale.embellishments.append(embellishment)
                except (ValueError, TypeError):
                    # Skip invalid IDs
                    continue
        
        # Update subscription sales count
        if subscription:
            subscription.sales_count += 1
        
        db.session.commit()
        flash('Sale recorded successfully!', 'success')
        return redirect(url_for('sales.index'))
    
    return render_template(
        'sales/new_sale.html',
        form=form,
        stores=stores,
        product_choices=product_choices_by_category
    )

@sales_bp.route('/view/<int:sale_id>')
@login_required
@company_required
def view_sale(sale_id):
    """View details of a specific sale"""
    company_id = current_user.company_id
    
    sale = Sale.query.filter_by(id=sale_id, company_id=company_id).first_or_404()
    
    return render_template('sales/view_sale.html', sale=sale)

@sales_bp.route('/edit/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_sale(sale_id):
    """Edit an existing sale"""
    company_id = current_user.company_id
    
    # Get the sale record and ensure it belongs to the user's company
    sale = Sale.query.filter_by(id=sale_id, company_id=company_id).first_or_404()
    
    # Get stores, categories, and products
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
    # Initialize the form
    form = SaleEntryForm(obj=sale)
    
    # Get product choices grouped by category
    product_choices_by_category = {}
    for category in categories:
        category_products = Product.query.filter_by(company_id=company_id, category_id=category.id).all()
        product_choices_by_category[category.id] = {
            'name': category.name,
            'products': [(product.id, product.name) for product in category_products]
        }
    
    # Set the product's category for the form
    product = None
    category_id = None
    if sale.product_id:
        product = Product.query.get(sale.product_id)
        if product:
            category_id = product.category_id
    
    # Set choices for the store dropdown
    form.store_id.choices = [(store.id, store.name) for store in stores]
    
    # Set the total price initially (cash + card)
    if not form.total_price.data:
        form.total_price.data = sale.cash_amount + sale.card_amount
    
    # Get available embellishments for this product
    available_embellishments = []
    selected_embellishments = [emb.id for emb in sale.embellishments]
    if product:
        available_embellishments = product.embellishments
    
    if form.validate_on_submit():
        # Update the sale
        sale.store_id = form.store_id.data
        sale.product_id = form.product_id.data
        sale.quantity = form.quantity.data
        sale.cash_amount = form.cash_amount.data
        sale.card_amount = form.card_amount.data
        sale.notes = form.notes.data if form.notes.data else None
        
        # Update embellishments
        sale.embellishments = []
        embellishment_ids = request.form.getlist('embellishment_ids')
        if embellishment_ids:
            for emb_id in embellishment_ids:
                try:
                    embellishment = Embellishment.query.get(int(emb_id))
                    if embellishment and embellishment.company_id == company_id:
                        sale.embellishments.append(embellishment)
                except (ValueError, TypeError):
                    # Skip invalid IDs
                    continue
        
        db.session.commit()
        flash('Sale updated successfully!', 'success')
        return redirect(url_for('sales.view_sale', sale_id=sale.id))
    
    return render_template(
        'sales/edit_sale.html',
        form=form,
        sale=sale,
        stores=stores,
        product_choices=product_choices_by_category,
        category_id=category_id,
        available_embellishments=available_embellishments,
        selected_embellishments=selected_embellishments
    )

@sales_bp.route('/delete/<int:sale_id>', methods=['POST'])
@login_required
@company_required
def delete_sale(sale_id):
    """Delete a sale"""
    company_id = current_user.company_id
    
    # Get the sale and check if it belongs to the user's company
    sale = Sale.query.filter_by(id=sale_id, company_id=company_id).first_or_404()
    
    # Delete the sale
    db.session.delete(sale)
    db.session.commit()
    
    flash('Sale deleted successfully!', 'success')
    return redirect(url_for('sales.index'))

@sales_bp.route('/locations')
@login_required
@company_required
def locations():
    """Sales by location view"""
    company_id = current_user.company_id
    
    # Get sales grouped by store
    stores = Store.query.filter_by(company_id=company_id).all()
    
    return render_template('sales/locations.html', stores=stores)

@sales_bp.route('/api/products/<int:category_id>')
@login_required
@company_required
def get_products(category_id):
    """Get products for a specific category (AJAX endpoint)"""
    company_id = current_user.company_id
    
    products = Product.query.filter_by(
        company_id=company_id,
        category_id=category_id
    ).all()
    
    product_list = [{'id': p.id, 'name': p.name} for p in products]
    return jsonify(product_list)

@sales_bp.route('/export')
@login_required
@company_required
def export_sales():
    """Export sales data to CSV (Admin only)"""
    company_id = current_user.company_id
    
    # Check if user is admin
    if current_user.role_company != 'admin':
        flash('Only company administrators can export sales data.', 'error')
        return redirect(url_for('sales.index'))
    
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid start date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('sales.export_form'))
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid end date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('sales.export_form'))
    
    try:
        # Create export service
        export_service = SalesImportExportService(company_id)
        
        # Generate CSV content
        csv_content = export_service.export_sales_to_csv(start_date, end_date)
        
        # Create response
        output = io.StringIO(csv_content)
        response = make_response(output.getvalue())
        
        # Set headers for file download
        filename = f"sales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        flash('Sales data exported successfully.', 'success')
        return response
        
    except Exception as e:
        flash(f'Error exporting sales data: {str(e)}', 'error')
        return redirect(url_for('sales.export_form'))

@sales_bp.route('/export/form')
@login_required
@company_required
def export_form():
    """Show export form (Admin only)"""
    company_id = current_user.company_id
    
    # Check if user is admin
    if current_user.role_company != 'admin':
        flash('Only company administrators can export sales data.', 'error')
        return redirect(url_for('sales.index'))
    
    return render_template('sales/export_form.html')

@sales_bp.route('/import', methods=['GET', 'POST'])
@login_required
@company_required
def import_sales():
    """Import sales data from CSV (Admin only)"""
    company_id = current_user.company_id
    
    # Check if user is admin
    if current_user.role_company != 'admin':
        flash('Only company administrators can import sales data.', 'error')
        return redirect(url_for('sales.index'))
    
    if request.method == 'GET':
        return render_template('sales/import_form.html')
    
    # Handle POST request
    action = request.form.get('action', 'preview')
    
    # Handle confirmed import (from preview page)
    if action == 'import':
        csv_content = request.form.get('csv_content', '')
        
        if not csv_content:
            flash('No CSV data found for import. Please try uploading the file again.', 'error')
            return render_template('sales/import_form.html')
        
        # Store CSV content in temporary file instead of session
        import_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f'import_{import_id}.csv')
        
        try:
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            # Store only the import ID and metadata in session
            session['import_id'] = import_id
            session['import_user_id'] = current_user.id
            session['import_company_id'] = company_id
            session['import_temp_file'] = temp_file_path
            
            # Redirect to progress page
            return redirect(url_for('sales.import_progress'))
            
        except Exception as e:
            flash(f'Error preparing import: {str(e)}', 'error')
            return render_template('sales/import_form.html')
    
    # Handle file upload for preview
    elif action == 'preview':
        # Check if we have csv_content in form data (alternative upload method)
        csv_content_from_form = request.form.get('csv_content', '').strip()
        if csv_content_from_form:
            try:
                # Create import service
                import_service = SalesImportExportService(company_id)
                
                # Validate CSV format first
                is_valid, validation_errors = import_service.validate_csv_format(csv_content_from_form)
                
                if not is_valid:
                    flash('CSV validation failed:', 'error')
                    for error in validation_errors:
                        flash(f'• {error}', 'error')
                    return render_template('sales/import_form.html')
                
                # Show preview of first few rows
                import csv
                import io as csv_io
                csv_reader = csv.DictReader(csv_io.StringIO(csv_content_from_form))
                preview_rows = []
                total_rows = 0
                for i, row in enumerate(csv_reader):
                    total_rows += 1
                    if i < 5:  # Show first 5 rows
                        preview_rows.append(row)
                
                return render_template('sales/import_preview.html', 
                                     preview_rows=preview_rows,
                                     headers=import_service.CSV_HEADERS,
                                     csv_content=csv_content_from_form,
                                     total_rows=total_rows)
                
            except Exception as e:
                flash(f'Error processing CSV data: {str(e)}', 'error')
                return render_template('sales/import_form.html')
        
        if 'csv_file' not in request.files:
            flash('No file selected. Please choose a CSV file to upload.', 'error')
            return render_template('sales/import_form.html')
        
        file = request.files['csv_file']
        
        if file.filename == '':
            flash('No file selected. Please choose a CSV file to upload.', 'error')
            return render_template('sales/import_form.html')
        
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file.', 'error')
            return render_template('sales/import_form.html')
        
        try:
            # Read file content
            csv_content = file.read().decode('utf-8')
            
            # Create import service
            import_service = SalesImportExportService(company_id)
            
            # Validate CSV format first
            is_valid, validation_errors = import_service.validate_csv_format(csv_content)
            
            if not is_valid:
                flash('CSV validation failed:', 'error')
                for error in validation_errors:
                    flash(f'• {error}', 'error')
                return render_template('sales/import_form.html')
            
            # Show preview of first few rows
            import csv
            import io as csv_io
            csv_reader = csv.DictReader(csv_io.StringIO(csv_content))
            preview_rows = []
            total_rows = 0
            for i, row in enumerate(csv_reader):
                total_rows += 1
                if i < 5:  # Show first 5 rows
                    preview_rows.append(row)
            
            return render_template('sales/import_preview.html', 
                                 preview_rows=preview_rows,
                                 headers=import_service.CSV_HEADERS,
                                 csv_content=csv_content,
                                 total_rows=total_rows)
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return render_template('sales/import_form.html')
    
    # If we get here, something unexpected happened
    flash('Invalid request. Please try again.', 'error')
    return render_template('sales/import_form.html')

@sales_bp.route('/import/progress')
@login_required
@company_required
def import_progress():
    """Show import progress page"""
    if current_user.role_company != 'admin':
        flash('Only company administrators can import sales data.', 'error')
        return redirect(url_for('sales.index'))
    
    # Check if we have import data in session
    if 'import_id' not in session:
        flash('No import data found. Please start the import process again.', 'error')
        return redirect(url_for('sales.import_sales'))
    
    return render_template('sales/import_progress.html')

@sales_bp.route('/import/execute', methods=['POST'])
@login_required
@company_required
def execute_import():
    """Execute the actual import with progress updates"""
    if current_user.role_company != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get import data from session
    import_id = session.get('import_id')
    temp_file_path = session.get('import_temp_file')
    user_id = session.get('import_user_id')
    company_id = session.get('import_company_id')
    
    if not import_id or not temp_file_path or not user_id or not company_id:
        return jsonify({'error': 'No import data found'}), 400
    
    # Read CSV content from temporary file
    try:
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
    except Exception as e:
        return jsonify({'error': f'Error reading import file: {str(e)}'}), 400
    
    try:
        # Initialize progress tracking
        session['import_progress'] = 0
        session['import_status'] = 'Starting import...'
        session['import_detail'] = 'Preparing to process data'
        
        # Create import service
        import_service = SalesImportExportService(company_id)
        
        # Count total rows for progress calculation
        import csv
        import io as csv_io
        csv_reader = csv.DictReader(csv_io.StringIO(csv_content))
        total_rows = sum(1 for _ in csv_reader)
        session['import_total_rows'] = total_rows
        
        # Execute import with progress tracking
        successful, failed, errors = import_service.import_sales_with_progress(
            csv_content, user_id, progress_callback=update_import_progress
        )
        
        # Final progress update
        session['import_progress'] = 100
        session['import_status'] = 'Import Complete!'
        session['import_detail'] = f'Processed {successful + failed} records'
        
        # Store results in session
        session['import_results'] = {
            'successful': successful,
            'failed': failed,
            'errors': errors[:10]
        }
        
        return jsonify({
            'success': True,
            'successful': successful,
            'failed': failed,
            'errors': errors[:10]  # Limit errors shown
        })
        
    except Exception as e:
        session['import_progress'] = 0
        session['import_status'] = 'Import Failed'
        session['import_detail'] = str(e)
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary file
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass  # Ignore cleanup errors

def update_import_progress(progress, status, detail=None):
    """Callback function to update import progress in session"""
    session['import_progress'] = progress
    session['import_status'] = status
    if detail:
        session['import_detail'] = detail

@sales_bp.route('/import/status')
@login_required
@company_required
def import_status():
    """Get import progress status"""
    if current_user.role_company != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get real progress from session
    progress = session.get('import_progress', 0)
    status = session.get('import_status', 'Initializing...')
    detail = session.get('import_detail', 'Starting import process')
    results = session.get('import_results')
    
    response = {
        'progress': progress,
        'status': status,
        'detail': detail
    }
    
    # Include results if import is complete
    if results:
        response['results'] = results
        # Clear session data after sending results
        temp_file_path = session.pop('import_temp_file', None)
        session.pop('import_id', None)
        session.pop('import_user_id', None)
        session.pop('import_company_id', None)
        session.pop('import_progress', None)
        session.pop('import_status', None)
        session.pop('import_detail', None)
        session.pop('import_results', None)
        session.pop('import_total_rows', None)
        
        # Clean up temporary file
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass  # Ignore cleanup errors
    
    return jsonify(response)

@sales_bp.route('/import/template')
@login_required
@company_required
def download_import_template():
    """Download CSV template for imports (Admin only)"""
    company_id = current_user.company_id
    
    # Check if user is admin
    if current_user.role_company != 'admin':
        flash('Only company administrators can access import templates.', 'error')
        return redirect(url_for('sales.index'))
    
    try:
        # Create template CSV with headers and sample data
        import_service = SalesImportExportService(company_id)
        
        output = io.StringIO()
        import csv
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(import_service.CSV_HEADERS)
        
        # Write sample data
        sample_row = [
            '2024-12-31',           # sale_date
            'Main Store',           # store_name
            'Jewelry',              # product_category
            'Silver Ring',          # product_name
            '1',                    # quantity
            '45.00',                # total
            '25.00',                # card_amount
            '20.00',                # cash_amount
            'Customer requested gift wrap'  # notes
        ]
        writer.writerow(sample_row)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=sales_import_template.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error generating template: {str(e)}', 'error')
        return redirect(url_for('sales.index')) 