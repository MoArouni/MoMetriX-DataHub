from datetime import datetime
from app import db

class Company(db.Model):
    """Company model that users belong to"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), unique=True, nullable=False)
    company_email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin relationship - separate from the members backref
    admin = db.relationship('User', foreign_keys=[admin_id], backref='administered_company', uselist=False)
    
    # Relationships defined in other models
    # employees - defined in User model
    # sales - defined in Sales model
    
    def __repr__(self):
        return f'<Company {self.company_name}>' 