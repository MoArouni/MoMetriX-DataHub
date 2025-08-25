from app import db
from datetime import datetime

class StockAdjustmentEntry(db.Model):
    """Model for tracking stock adjustments needed when products are sold"""
    __tablename__ = 'stock_adjustment_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    
    # Product details (for tracking even if product is deleted)
    product_name = db.Column(db.String(200), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    
    # Sale details
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    

    
    # Adjustment tracking
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company')
    product = db.relationship('Product')
    sale = db.relationship('Sale')
    completed_by_user = db.relationship('User', foreign_keys=[completed_by])
    
    def __repr__(self):
        return f'<StockAdjustmentEntry {self.product_name} - Qty: {self.quantity_sold}>'
    
    @property
    def total_items_to_adjust(self):
        """Calculate total items that need stock adjustment"""
        return self.quantity_sold
    
    @property
    def adjustment_description(self):
        """Get human-readable description of the adjustment needed"""
        return f"{self.quantity_sold} unit(s) of {self.product_name}" 