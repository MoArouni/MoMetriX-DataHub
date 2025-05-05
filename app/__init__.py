from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

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
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500 