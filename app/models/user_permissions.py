from app import db
from datetime import datetime

class UserPermissions(db.Model):
    """Model for storing granular user permissions"""
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Store permissions - which stores the user can access
    allowed_stores = db.Column(db.Text, nullable=True)  # JSON array of store IDs
    
    # Sales data range permissions
    data_range_access = db.Column(db.String(50), default='current_day')  # current_day, week, month, all_time
    
    # Permission levels
    can_view_sales = db.Column(db.Boolean, default=True)
    can_add_sales = db.Column(db.Boolean, default=True)
    can_edit_sales = db.Column(db.Boolean, default=False)
    can_delete_sales = db.Column(db.Boolean, default=False)
    can_view_analytics = db.Column(db.Boolean, default=False)
    can_export_data = db.Column(db.Boolean, default=False)
    can_manage_products = db.Column(db.Boolean, default=True)
    can_manage_stores = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='permissions')
    company = db.relationship('Company')
    
    def __repr__(self):
        return f'<UserPermissions {self.user_id} in Company {self.company_id}>'
    
    @property
    def allowed_store_ids(self):
        """Get allowed store IDs as a list"""
        if self.allowed_stores:
            import json
            try:
                return json.loads(self.allowed_stores)
            except:
                return []
        return []
    
    @allowed_store_ids.setter
    def allowed_store_ids(self, store_ids):
        """Set allowed store IDs from a list"""
        import json
        self.allowed_stores = json.dumps(store_ids) if store_ids else None
    
    def has_store_access(self, store_id):
        """Check if user has access to a specific store"""
        allowed_ids = self.allowed_store_ids
        return not allowed_ids or store_id in allowed_ids
    
    def get_data_range_description(self):
        """Get human-readable description of data range access"""
        descriptions = {
            'current_day': 'Current Day Only',
            'week': 'Past Week',
            'month': 'Past Month',
            'all_time': 'All Historical Data'
        }
        return descriptions.get(self.data_range_access, 'Unknown') 