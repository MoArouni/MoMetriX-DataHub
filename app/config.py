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
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Server configuration for URL generation
    SERVER_NAME = os.environ.get('SERVER_NAME')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME')
    
    # Environment-specific settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', 'on', '1']
    TESTING = os.environ.get('FLASK_TESTING', 'false').lower() in ['true', 'on', '1']
    
    # Database URL - use exactly what's provided
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Admin user settings for initial setup
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_SUBJECT_PREFIX = '[MoMetriX DataHub] '
    MAIL_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Contact information for footer and contact forms
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL')
    CONTACT_PHONE = os.environ.get('CONTACT_PHONE')
    CONTACT_ADDRESS = os.environ.get('CONTACT_ADDRESS')
    COMPANY_NAME = os.environ.get('COMPANY_NAME')
    
    # Social media links
    SOCIAL_TWITTER = os.environ.get('SOCIAL_TWITTER')
    SOCIAL_LINKEDIN = os.environ.get('SOCIAL_LINKEDIN')
    SOCIAL_GITHUB = os.environ.get('SOCIAL_GITHUB')
    SOCIAL_INSTAGRAM = os.environ.get('SOCIAL_INSTAGRAM')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
class TestingConfig(Config):
    """Testing config"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    """Production config"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Fix for legacy "postgres://" vs "postgresql://" URL format (Render uses postgresql://)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
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
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Config dictionary mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 