import os
from datetime import timedelta
import urllib.parse

basedir = os.path.abspath(os.path.dirname(__file__))

# Helper function to safely handle None values in connection string
def safe_quote(value):
    if value is None:
        return ""
    return urllib.parse.quote_plus(str(value))

class Config:
    """Base config class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Server configuration for URL generation
    SERVER_NAME = os.environ.get('SERVER_NAME')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    
    # Environment-specific settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', 'on', '1']
    TESTING = os.environ.get('FLASK_TESTING', 'false').lower() in ['true', 'on', '1']
    DB_NAME = os.environ.get('DB_NAME', 'MoMetriXHub')  # Default to MoMetriXHub
    
    # Database settings - used if DATABASE_URL is not set
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    
    # Check and fix DATABASE_URL format if it exists
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        if 'MoMetriXHub' not in DATABASE_URL:
            # If DATABASE_URL exists but doesn't have the right database name
            parts = DATABASE_URL.rsplit('/', 1)
            if len(parts) > 1:
                DATABASE_URL = f"{parts[0]}/MoMetriXHub"
                os.environ['DATABASE_URL'] = DATABASE_URL
    else:
        # Build default PostgreSQL URL if DATABASE_URL is not provided
        DATABASE_URL = f"postgresql://{DB_USER}:{safe_quote(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Admin user settings for initial setup
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'adminpassword')
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_SUBJECT_PREFIX = '[MoMetriX DataHub] '
    MAIL_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Contact information for footer and contact forms
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'contact@example.com')
    CONTACT_PHONE = os.environ.get('CONTACT_PHONE', '+1 (555) 123-4567')
    CONTACT_ADDRESS = os.environ.get('CONTACT_ADDRESS', 'Your Business Address')
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'MoMetriX DataHub')
    
    # Social media links
    SOCIAL_TWITTER = os.environ.get('SOCIAL_TWITTER', 'https://twitter.com/yourcompany')
    SOCIAL_LINKEDIN = os.environ.get('SOCIAL_LINKEDIN', 'https://linkedin.com/company/yourcompany')
    SOCIAL_GITHUB = os.environ.get('SOCIAL_GITHUB', 'https://github.com/yourcompany')
    SOCIAL_INSTAGRAM = os.environ.get('SOCIAL_INSTAGRAM', 'https://instagram.com/yourcompany')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True
    # Use the DATABASE_URL from Config
    SQLALCHEMY_DATABASE_URI = Config.DATABASE_URL
    
class TestingConfig(Config):
    """Testing config"""
    TESTING = True
    # Create a test-specific DATABASE_URL using the same credentials but different database name
    DB_NAME = os.environ.get('TEST_DB_NAME', 'MoMetriXHub_test')
    SQLALCHEMY_DATABASE_URI = (os.environ.get('TEST_DATABASE_URL') or 
        f"postgresql://{Config.DB_USER}:{safe_quote(Config.DB_PASSWORD)}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}")
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    """Production config"""
    # Use the DATABASE_URL from Config
    SQLALCHEMY_DATABASE_URI = Config.DATABASE_URL
    
    # Fix for Heroku's "postgres://" vs "postgresql://" URL format
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
        
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_test_key')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_your_test_key')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')

# Config dictionary mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 