from flask import Blueprint, render_template

# Create blueprint
policies_bp = Blueprint('policies', __name__, url_prefix='/policies')

@policies_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('policies/privacy.html')

@policies_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('policies/terms.html')

@policies_bp.route('/cookies')
def cookies():
    """Cookie Policy page"""
    return render_template('policies/cookies.html')

@policies_bp.route('/data-protection')
def data_protection():
    """Data Protection Policy page"""
    return render_template('policies/data_protection.html')

@policies_bp.route('/acceptable-use')
def acceptable_use():
    """Acceptable Use Policy page"""
    return render_template('policies/acceptable_use.html') 