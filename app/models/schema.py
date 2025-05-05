from app import db

class CompanySchema(db.Model):
    """Model for company-specific dynamic form fields"""
    __tablename__ = 'company_schema'
    
    schema_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, number, select, date, etc.
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=True)
    is_required = db.Column(db.Boolean, default=True)
    default_value = db.Column(db.String(255), nullable=True)  # Optional default value for the field
    options = db.Column(db.Text, nullable=True)  # JSON string for select options
    display_order = db.Column(db.Integer, default=0)  # For ordering fields in forms
    
    # Relationships
    company = db.relationship('Company', backref='schema_fields')
    category = db.relationship('ProductCategory', backref='schema_fields')
    
    def __repr__(self):
        return f'<CompanySchema {self.field_name} - {self.field_type}>' 