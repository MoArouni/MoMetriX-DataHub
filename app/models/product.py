from app import db
from decimal import Decimal
import json
from datetime import datetime

class Embellishment(db.Model):
    """Embellishment model for product customizations"""
    __tablename__ = 'embellishments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('embellishments', lazy='dynamic'))
    product_types = db.relationship('ProductCategory', secondary='embellishment_product_types', 
                                   backref=db.backref('embellishments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Embellishment {self.name}>'

# Association table between products and embellishments
product_embellishments = db.Table('product_embellishments',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('embellishment_id', db.Integer, db.ForeignKey('embellishments.id'), primary_key=True)
)

# Association table between embellishments and product types (categories)
db.Table('embellishment_product_types',
    db.Column('embellishment_id', db.Integer, db.ForeignKey('embellishments.id'), primary_key=True),
    db.Column('product_type_id', db.Integer, db.ForeignKey('product_categories.id'), primary_key=True)
)

# Association table between sales and embellishments
sale_embellishments = db.Table('sale_embellishments',
    db.Column('sale_id', db.Integer, db.ForeignKey('sales.id'), primary_key=True),
    db.Column('embellishment_id', db.Integer, db.ForeignKey('embellishments.id'), primary_key=True)
)

class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    base_price = db.Column(db.Numeric(10, 2), default=0.00)
    _additional_fields = db.Column('additional_fields', db.Text, nullable=True)  # JSON string for dynamic fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('products', lazy='dynamic'))
    sales = db.relationship('Sale', backref='product', lazy='dynamic')
    embellishments = db.relationship('Embellishment', secondary=product_embellishments, 
                                    backref=db.backref('products', lazy='dynamic'))
    
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