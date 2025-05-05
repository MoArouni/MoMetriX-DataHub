from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_
from app import db
from app.models.store import Store
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.sales import Sale, ProductFeature, FeatureRegistry
from app.forms.sales_setup_forms import SaleEntryForm
from app.utils.decorators import company_required, subscriber_required
from datetime import datetime, date
import json

# Create blueprint
sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
@login_required
@company_required
def index():
    """Sales dashboard"""
    company_id = current_user.company_id
    
    # Check if company has stores, categories, and products set up
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    
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
        category_count=len(categories)
    )

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
@company_required
def new_sale():
    """Create a new sale entry"""
    company_id = current_user.company_id
    
    # Check if company has necessary setup
    stores = Store.query.filter_by(company_id=company_id).all()
    categories = ProductCategory.query.filter_by(company_id=company_id).all()
    products = Product.query.filter_by(company_id=company_id).all()
    
    if not stores or not categories or not products:
        flash('Please complete your sales database setup first.', 'warning')
        return redirect(url_for('sales_setup.setup_stores'))
    
    form = SaleEntryForm()
    
    # Populate dropdown choices
    form.store_id.choices = [(store.id, store.name) for store in stores]
    
    # Get product choices grouped by category
    product_choices_by_category = {}
    for category in categories:
        category_products = Product.query.filter_by(company_id=company_id, category_id=category.id).all()
        product_choices_by_category[category.id] = {
            'name': category.name,
            'products': [(product.id, product.name) for product in category_products]
        }
    
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
        
        # Process dynamic product features
        feature_names = request.form.getlist('feature_name[]')
        feature_values = request.form.getlist('feature_value[]')
        
        for i in range(len(feature_names)):
            if feature_names[i] and feature_values[i]:
                # Add to product features
                feature = ProductFeature(
                    sale_id=new_sale.id,
                    company_id=company_id,
                    name=feature_names[i],
                    value=feature_values[i]
                )
                db.session.add(feature)
                
                # Update feature registry
                registry_entry = FeatureRegistry.query.filter_by(
                    company_id=company_id,
                    name=feature_names[i],
                    value=feature_values[i]
                ).first()
                
                if registry_entry:
                    registry_entry.usage_count += 1
                    registry_entry.updated_at = datetime.utcnow()
                else:
                    registry_entry = FeatureRegistry(
                        company_id=company_id,
                        name=feature_names[i],
                        value=feature_values[i]
                    )
                    db.session.add(registry_entry)
        
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
    features = ProductFeature.query.filter_by(sale_id=sale_id).all()
    
    return render_template('sales/view_sale.html', sale=sale, features=features)

@sales_bp.route('/locations')
@login_required
@company_required
def locations():
    """Manage store locations"""
    company_id = current_user.company_id
    
    # Get all store locations for this company
    stores = Store.query.filter_by(company_id=company_id).order_by(Store.name).all()
    
    return render_template('sales/locations.html', stores=stores)

@sales_bp.route('/api/products/<int:category_id>')
@login_required
@company_required
def get_products(category_id):
    """API to get products by category"""
    company_id = current_user.company_id
    
    products = Product.query.filter_by(
        company_id=company_id,
        category_id=category_id
    ).all()
    
    result = [{'id': product.id, 'name': product.name} for product in products]
    return jsonify(result) 