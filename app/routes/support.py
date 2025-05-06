from flask import Blueprint, render_template

support_bp = Blueprint('support', __name__, url_prefix='/support')

@support_bp.route('/')
def index():
    """Render the support page."""
    return render_template('support/index.html') 