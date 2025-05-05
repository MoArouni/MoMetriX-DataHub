from flask import Blueprint

def create_scalable_app():
    """
    Factory function to create and configure the scalable_app Blueprint.
    """
    # Create the Blueprint and specify the template folder
    scalable_bp = Blueprint('scalable', __name__, template_folder='../templates')

    # Register routes from each subfolder
    from .main.routes import register_routes as register_main_routes
    from .auth.routes import register_routes as register_auth_routes
    from .companies.routes import register_routes as register_companies_routes
    from .analysis.routes import register_routes as register_analysis_routes

    register_main_routes(scalable_bp)
    register_auth_routes(scalable_bp)
    register_companies_routes(scalable_bp)
    register_analysis_routes(scalable_bp)
    # Register the static folder for the Blueprint
    scalable_bp.static_folder = '../static'
    scalable_bp.static_url_path = '/static'



    return scalable_bp