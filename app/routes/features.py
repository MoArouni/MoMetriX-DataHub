from flask import Blueprint, render_template

features_bp = Blueprint('features', __name__, url_prefix='/features')

@features_bp.route('/')
def index():
    """Render the features/mission page."""
    return render_template('features/index.html') 