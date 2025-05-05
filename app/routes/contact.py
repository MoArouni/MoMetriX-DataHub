from flask import Blueprint, render_template
from flask_login import current_user

# Create blueprint
contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/', methods=['GET'])
def index():
    """Contact page route - Using Formspree for form submission"""
    return render_template('contact/index.html')

@contact_bp.route('/thank-you', methods=['GET'])
def thank_you():
    """Thank you page after successful form submission"""
    return render_template('contact/thank_you.html') 