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

@login_manager.user_loader
def load_user(user_id):
    """User loader function for Flask-Login"""
    return User.query.get(int(user_id)) 