from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
from time import time
import jwt
from flask import current_app

from app import db, login_manager

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    role_website = db.Column(db.String(20), db.ForeignKey('role_website.role_name'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    role_company = db.Column(db.String(20), db.ForeignKey('role_company.role_name'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True, index=True)
    
    # Settings
    email_notifications = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(2), default='en')
    
    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id], backref='members')
    blog_posts = db.relationship('BlogPost', backref='author', lazy='dynamic')
    
    # Simplified Q&A relationships
    questions = db.relationship('Question', backref='author', lazy=True)
    answers = db.relationship('Answer', backref='author', lazy=True)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
        
    @classmethod
    def can_create_admin(cls):
        """Check if an admin can be created by checking if any admin exists"""
        admin_exists = cls.query.filter_by(is_admin=True).first() is not None
        return not admin_exists
        
    def save(self):
        """Save the user to database with admin check"""
        if self.is_admin and not User.can_create_admin():
            self.is_admin = False
            self.role_website = 'subscriber'
        db.session.add(self)
        db.session.commit()
        
    def generate_reset_token(self, expires_in=3600):
        """Generate a JWT token for password reset
        
        Args:
            expires_in: Token expiry time in seconds (default: 1 hour)
            
        Returns:
            str: JWT token
        """
        token_payload = {
            'reset_password': self.id,
            'exp': time() + expires_in
        }
        return jwt.encode(
            token_payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_token(token):
        """Verify a password reset token
        
        Args:
            token: JWT token to verify
            
        Returns:
            User or None: User instance if token is valid, None otherwise
        """
        try:
            data = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except:
            return None
        
        user_id = data.get('reset_password')
        if user_id is None:
            return None
            
        return User.query.get(user_id)

    def generate_email_verification_token(self, expires_in=3600):
        """Generate a JWT token for email verification
        
        Args:
            expires_in: Token expiry time in seconds (default: 1 hour)
            
        Returns:
            str: JWT token
        """
        token_payload = {
            'verify_email': self.id,
            'exp': time() + expires_in
        }
        token = jwt.encode(
            token_payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        self.email_verification_token = token
        return token
    
    @staticmethod
    def verify_email_token(token):
        """Verify an email verification token
        
        Args:
            token: JWT token to verify
            
        Returns:
            User or None: User instance if token is valid, None otherwise
        """
        try:
            data = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except:
            return None
        
        user_id = data.get('verify_email')
        if user_id is None:
            return None
            
        user = User.query.get(user_id)
        if user and user.email_verification_token == token:
            return user
        return None
    
    def verify_email(self):
        """Mark email as verified and clear verification token"""
        self.email_verified = True
        self.email_verification_token = None
        db.session.commit()

    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username  # Fallback to username if no name is set

    def has_permission(self, perm):
        """Check if user has a specific permission"""
        # Site admins have all permissions
        if self.is_admin:
            return True
        
        # Company admins have all permissions within their company
        if self.company_id and self.company and self.company.admin_id == self.id:
            return True
        
        # For other users, check their specific permissions
        if not self.company_id:
            return False
        
        # Import here to avoid circular imports
        from app.models.user_permissions import UserPermissions
        
        permissions = UserPermissions.query.filter_by(
            user_id=self.id,
            company_id=self.company_id
        ).first()
        
        if not permissions:
            return False
        
        # Map permission names to UserPermissions attributes
        permission_map = {
            'analytics': permissions.can_view_analytics,
            'manage_products': permissions.can_manage_products,
            'manage_stores': permissions.can_manage_stores,
            'view_sales': permissions.can_view_sales,
            'add_sales': permissions.can_add_sales,
            'edit_sales': permissions.can_edit_sales,
            'delete_sales': permissions.can_delete_sales,
            'export_data': permissions.can_export_data,
        }
        
        return permission_map.get(perm, False)

@login_manager.user_loader
def load_user(user_id):
    """User loader function for Flask-Login"""
    return User.query.get(int(user_id)) 