from app import db

class RoleWebsite(db.Model):
    """Website role for users (admin, moderator, subscriber, viewer)"""
    __tablename__ = 'role_website'
    
    role_name = db.Column(db.String(20), primary_key=True)
    
    # Relationship with users
    users = db.relationship('User', backref='website_role', lazy='dynamic')
    
    def __repr__(self):
        return f'<RoleWebsite {self.role_name}>'

class RoleCompany(db.Model):
    """Company role for users (admin, moderator)"""
    __tablename__ = 'role_company'
    
    role_name = db.Column(db.String(20), primary_key=True)
    
    # Relationship with users
    users = db.relationship('User', backref='company_role', lazy='dynamic')
    
    def __repr__(self):
        return f'<RoleCompany {self.role_name}>' 