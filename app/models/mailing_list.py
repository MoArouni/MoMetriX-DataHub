from datetime import datetime
from app import db

class MailingList(db.Model):
    """Model for storing email subscribers to newsletter and updates"""
    __tablename__ = 'mailing_list'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<MailingList {self.email}>' 