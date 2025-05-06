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
    _additional_fields = db.Column('additional_fields', db.Text, nullable=True)  # JSON string for dynamic fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('products', lazy='dynamic'))
    sales = db.relationship('Sale', backref='product', lazy='dynamic')
    
    @property
    def additional_fields(self):
        """Get the deserialized additional fields"""
        if self._additional_fields:
            return json.loads(self._additional_fields)
        return {}
    
    @additional_fields.setter
    def additional_fields(self, value):
        """Store the serialized additional fields"""
        if value is None:
            self._additional_fields = None
        elif isinstance(value, str):
            self._additional_fields = value
        else:
            self._additional_fields = json.dumps(value)
    
    def __repr__(self):
        return f'<Product {self.name}>' 