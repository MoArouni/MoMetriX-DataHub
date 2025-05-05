from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_mail import Mail
from werkzeug.exceptions import HTTPException

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.tools import tools_bp
    from app.routes.blog import blog
    from app.routes.pricing import pricing
    from app.routes.settings import settings
    from app.routes.qa import qa
    from app.routes.upload import upload_bp
    from app.routes.products import products_bp
    from app.routes.sales import sales_bp
    from app.routes.sales_setup import sales_setup_bp
    from app.routes.schema import schema_bp
    from app.routes.admin import admin_bp
    from app.routes.subscription import subscription_bp
    from app.routes.contact import contact_bp
    from app.routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(blog)
    app.register_blueprint(pricing)
    app.register_blueprint(settings)
    app.register_blueprint(qa)
    app.register_blueprint(upload_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(sales_setup_bp)
    app.register_blueprint(schema_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(user_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize database with default values
    with app.app_context():
        from app.utils.db_init import init_roles
        init_roles()
    
    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers with the Flask application"""
    
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html', 
                              error_message=str(e),
                              error_details=getattr(e, 'description', None)), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template('errors/401.html', error_message=str(e)), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', error_message=str(e)), 403
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html', error_message=str(e)), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template('errors/405.html', error_message=str(e)), 405
    
    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html', error_message=str(e)), 429
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', error_message=str(e)), 500
    
    # Handle CSRF errors
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', 
                              error_message="CSRF Token Error", 
                              error_details=e.description), 400
    
    # Catch-all for other HTTP errors
    @app.errorhandler(Exception)
    def handle_exception(e):
        # If the exception is a HTTPException, use the specific error page
        if isinstance(e, HTTPException):
            if e.code in [400, 401, 403, 404, 405, 429, 500]:
                # Already handled by specific handlers
                return e
            
            # Use generic template for other HTTP errors
            return render_template('errors/generic.html',
                                   code=e.code,
                                   title=e.name,
                                   error_message=e.description), e.code
        
        # For non-HTTP exceptions, use 500 template
        app.logger.error(f"Unhandled exception: {str(e)}")
        return render_template('errors/500.html'), 500