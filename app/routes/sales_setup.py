from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models.company import Company
from app.models.store import Store
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.forms.sales_setup_forms import CompanySetupForm, CategoriesSetupForm, StoresSetupForm, ProductsSetupForm
from app.utils.decorators import company_required
import logging

# Create blueprint
sales_setup_bp = Blueprint('sales_setup', __name__, url_prefix='/sales/setup')

@sales_setup_bp.route('/')
@login_required
def setup_wizard():
    """Main setup wizard page (redirects to dashboard)"""
    # Redirect to dashboard
    flash('The setup wizard has been simplified. Please use the dashboard to manage your company, stores, categories, and products.', 'info')
    return redirect(url_for('dashboard.dashboard'))

@sales_setup_bp.route('/company', methods=['GET', 'POST'])
@login_required
def setup_company():
    """Setup company - redirects to dashboard create company"""
    return redirect(url_for('dashboard.create_company'))

@sales_setup_bp.route('/stores', methods=['GET', 'POST'])
@login_required
@company_required
def setup_stores():
    """Setup stores - redirects to stores management"""
    return redirect(url_for('stores.manage'))

@sales_setup_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@company_required
def setup_categories():
    """Setup product categories - redirects to products categories management"""
    return redirect(url_for('products.categories'))

@sales_setup_bp.route('/products', methods=['GET', 'POST'])
@login_required
@company_required
def setup_products():
    """Setup products - redirects to products management"""
    return redirect(url_for('products.index'))

@sales_setup_bp.route('/products/<int:category_id>', methods=['GET', 'POST'])
@login_required
@company_required
def setup_category_products(category_id):
    """Setup products for a specific category - redirects to category products management"""
    return redirect(url_for('products.category_products', category_id=category_id))

@sales_setup_bp.route('/payment', methods=['GET', 'POST'])
@login_required
@company_required
def setup_payment():
    """Setup payment - redirects to dashboard"""
    flash('Payment setup has been integrated into your company settings.', 'info')
    return redirect(url_for('dashboard.dashboard'))

@sales_setup_bp.route('/mods', methods=['GET', 'POST'])
@login_required
@company_required
def setup_mods():
    """Setup mods - redirects to dashboard"""
    flash('Modifiers setup has been integrated into your product management.', 'info')
    return redirect(url_for('products.index'))

@sales_setup_bp.route('/complete')
@login_required
@company_required
def setup_complete():
    """Setup complete - redirects to dashboard"""
    flash('Setup complete! You can now start recording sales.', 'success')
    return redirect(url_for('dashboard.dashboard'))