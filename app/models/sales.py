from app import db
from datetime import date, datetime
import json
from app.models.product import sale_embellishments  # Import the association table

class Sale(db.Model):
    """Sale model representing a transaction - matches CSV structure exactly"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Direct CSV fields - matching your newfile.csv structure exactly
    sale_date = db.Column(db.Date, nullable=False, default=date.today)
    store_name = db.Column(db.String(200), nullable=False)
    product_category = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    card_amount = db.Column(db.Numeric(10, 2), default=0.00)
    cash_amount = db.Column(db.Numeric(10, 2), default=0.00)
    notes = db.Column(db.Text)
    
    # Keep relationships for backward compatibility (optional)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('sales', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('sales', lazy='dynamic'))
    # Note: 'store' and 'product' relationships are created by backrefs from Store and Product models
    embellishments = db.relationship('Embellishment', secondary=sale_embellishments,
                                   backref=db.backref('sales', lazy='dynamic'))
    
    @property
    def total_amount(self):
        """Return the total amount with fallback calculation"""
        if self.total is not None:
            return self.total
        # Fallback to calculating from card and cash amounts
        card = self.card_amount or 0
        cash = self.cash_amount or 0
        return card + cash
    
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
        return f'<Sale {self.id} - {self.store_name} - {self.product_name} - {self.total}>'

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