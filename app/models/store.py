from app import db
from datetime import datetime

class Store(db.Model):
    """Store model for company locations where sales occur"""
    __tablename__ = 'stores'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('stores', lazy='dynamic'))
    sales = db.relationship('Sale', backref='store', lazy='dynamic')
    
    def __repr__(self):
        return f'<Store {self.name}>' 