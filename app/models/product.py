from app import db
from decimal import Decimal
import json
from datetime import datetime

class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    base_price = db.Column(db.Numeric(10, 2), default=0.00)
    active = db.Column(db.Boolean, default=True)
    additional_fields = db.Column(db.Text, nullable=True)  # JSON string for dynamic fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('products', lazy='dynamic'))
    sales = db.relationship('Sale', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.name}>' 