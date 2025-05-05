from datetime import datetime
import json
from app import db

class Tool(db.Model):
    """Tool model for data analysis tools created by users"""
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    schema = db.Column(db.Text)  # Stored as JSON string
    config = db.Column(db.Text)  # Stored as JSON string
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('tools', lazy='dynamic'))
    
    @property
    def schema_dict(self):
        """Return schema as dictionary"""
        if self.schema:
            return json.loads(self.schema)
        return {}
        
    @schema_dict.setter
    def schema_dict(self, schema_dict):
        """Set schema from dictionary"""
        self.schema = json.dumps(schema_dict)
        
    @property
    def config_dict(self):
        """Return config as dictionary"""
        if self.config:
            return json.loads(self.config)
        return {}
        
    @config_dict.setter
    def config_dict(self, config_dict):
        """Set config from dictionary"""
        self.config = json.dumps(config_dict)
    
    def __repr__(self):
        return f'<Tool {self.name}>' 