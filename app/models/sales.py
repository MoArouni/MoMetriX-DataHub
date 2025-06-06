from app import db
from datetime import date, datetime
import json
from app.models.product import sale_embellishments  # Import the association table

class Sale(db.Model):
    """Sale model representing a transaction"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    sale_date = db.Column(db.Date, nullable=False, default=date.today)
    quantity = db.Column(db.Integer, nullable=False)
    card_amount = db.Column(db.Numeric(10, 2), default=0.00)
    cash_amount = db.Column(db.Numeric(10, 2), default=0.00)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('sales', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('sales', lazy='dynamic'))
    # store and product relationships are defined in their respective models
    embellishments = db.relationship('Embellishment', secondary=sale_embellishments,
                                   backref=db.backref('sales', lazy='dynamic'))
    
    @property
    def total_amount(self):
        """Calculate the total amount from card and cash amounts"""
        return self.card_amount + self.cash_amount
    
    @property
    def payment_method(self):
        """Determine payment method based on amounts"""
        if self.card_amount > 0 and self.cash_amount > 0:
            return "Both (Card + Cash)"
        elif self.card_amount > 0:
            return "Card"
        elif self.cash_amount > 0:
            return "Cash"
        else:
            return "Unknown"
    
    def __repr__(self):
        return f'<Sale {self.id} - {self.total_amount}>'

class SaleItem(db.Model):
    """Individual items in a sale"""
    __tablename__ = 'sale_items'
    
    item_id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.00)
    tax_percentage = db.Column(db.Numeric(5, 2), default=0.00)
    is_combo = db.Column(db.Boolean, default=False)
    _combo_details = db.Column(db.Text, name='combo_details')
    
    @property
    def combo_details(self):
        if self._combo_details:
            return json.loads(self._combo_details)
        return None
    
    @combo_details.setter
    def combo_details(self, value):
        if value:
            self._combo_details = json.dumps(value)
        else:
            self._combo_details = None
    
    def __repr__(self):
        return f'<SaleItem {self.item_id}>' 