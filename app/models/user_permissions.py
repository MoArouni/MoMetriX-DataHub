from app import db
from datetime import datetime

class UserPermissions(db.Model):
    """Model for storing granular user permissions"""
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # 2 Simple Permission Settings:
    # 1. What can they do: daily_sales (add/see daily) or see_everything (see everything)
    access_level = db.Column(db.String(50), default='daily_sales')  # daily_sales, see_everything
    
    # 2. Store access - which stores they can access
    allowed_stores = db.Column(db.Text, nullable=True)  # JSON array of store IDs
    
    # Auto-calculated permissions based on the 3 settings above
    can_view_sales = db.Column(db.Boolean, default=True)
    can_add_sales = db.Column(db.Boolean, default=True)
    can_edit_sales = db.Column(db.Boolean, default=True)
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
    
    def set_permissions(self, access_level, allowed_store_ids=None):
        """Set permissions based on the 2 simple settings"""
        self.access_level = access_level
        self.allowed_store_ids = allowed_store_ids or []
        
        # Auto-calculate individual permissions
        if access_level == 'daily_sales':
            # Can add and see their own daily sales only - NO analytics
            self.can_view_sales = True
            self.can_add_sales = True
            self.can_edit_sales = True
            self.can_delete_sales = False
            self.can_view_analytics = False  # NO analytics access
            self.can_export_data = False
            self.can_manage_products = True
            self.can_manage_stores = False
            
        elif access_level == 'see_everything':
            # Can see everything and do everything
            self.can_view_sales = True
            self.can_add_sales = True
            self.can_edit_sales = True
            self.can_delete_sales = True
            self.can_view_analytics = True
            self.can_export_data = True
            self.can_manage_products = True
            self.can_manage_stores = True
    
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
    
    def get_access_level_description(self):
        """Get human-readable description of access level"""
        descriptions = {
            'daily_sales': 'Add & See Daily Sales Only',
            'see_everything': 'See Everything'
        }
        return descriptions.get(self.access_level, 'Unknown')
    
    def get_data_range_description(self):
        """Get human-readable description of data access range"""
        # Since we removed data_range, just return access level info
        if self.access_level == 'daily_sales':
            return 'Daily sales only'
        elif self.access_level == 'see_everything':
            return 'All data access'
        return 'Limited access' 