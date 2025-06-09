from datetime import datetime, timedelta
from app import db
import secrets
import string

class EmailVerificationCode(db.Model):
    """Model for storing email verification codes"""
    __tablename__ = 'email_verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    def __init__(self, email):
        self.email = email.lower()
        self.code = self.generate_code()
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @property
    def is_expired(self):
        """Check if the verification code has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the verification code is valid (not expired and not used)"""
        return not self.is_expired and not self.is_used
    
    def mark_as_used(self):
        """Mark the verification code as used"""
        self.is_used = True
        db.session.commit()
    
    @classmethod
    def verify_code(cls, email, code):
        """Verify an email verification code"""
        verification = cls.query.filter_by(
            email=email.lower(),
            code=code,
            is_used=False
        ).first()
        
        if verification and verification.is_valid:
            verification.mark_as_used()
            return True
        return False
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired verification codes"""
        expired_codes = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for code in expired_codes:
            db.session.delete(code)
        db.session.commit()

class JoinRequest(db.Model):
    """Model for storing company join requests"""
    __tablename__ = 'join_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    username = db.Column(db.String(64), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    company = db.relationship('Company', backref='join_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def approve(self, admin_user):
        """Approve the join request"""
        self.status = 'approved'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = admin_user.id
        db.session.commit()
    
    def decline(self, admin_user):
        """Decline the join request"""
        self.status = 'declined'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = admin_user.id
        db.session.commit()
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_declined(self):
        return self.status == 'declined'
    
    @property
    def full_name(self):
        """Get the full name of the requester"""
        return f"{self.first_name} {self.last_name}"

class ModeratorInvite(db.Model):
    """Model for storing moderator invites with tokens and passcodes"""
    __tablename__ = 'moderator_invites'
    
    id = db.Column(db.Integer, primary_key=True)
    join_request_id = db.Column(db.Integer, db.ForeignKey('join_requests.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    invite_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    passcode = db.Column(db.String(6), nullable=False)
    role_permissions = db.Column(db.String(50), nullable=False)  # data_entry, daily_sales, full_access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    passcode_expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    join_request = db.relationship('JoinRequest', backref='invite')
    company = db.relationship('Company')
    
    def __init__(self, join_request_id, email, company_id, role_permissions):
        self.join_request_id = join_request_id
        self.email = email.lower()
        self.company_id = company_id
        self.role_permissions = role_permissions
        self.invite_token = self.generate_token()
        self.passcode = self.generate_passcode()
        self.expires_at = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes for invite link
        self.passcode_expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5 minutes for passcode
    
    @staticmethod
    def generate_token():
        """Generate a secure invite token"""
        return secrets.token_urlsafe(48)
    
    @staticmethod
    def generate_passcode():
        """Generate a 6-digit passcode"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @property
    def is_expired(self):
        """Check if the invite has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_passcode_expired(self):
        """Check if the passcode has expired"""
        return datetime.utcnow() > self.passcode_expires_at
    
    @property
    def is_valid(self):
        """Check if the invite is valid (not expired and not used)"""
        return not self.is_expired and not self.is_used
    
    def mark_as_used(self):
        """Mark the invite as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def verify_invite(cls, token, passcode):
        """Verify an invite token and passcode"""
        invite = cls.query.filter_by(
            invite_token=token,
            is_used=False
        ).first()
        
        if invite and invite.is_valid and not invite.is_passcode_expired and invite.passcode == passcode:
            return invite
        return None
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired invites"""
        expired_invites = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for invite in expired_invites:
            db.session.delete(invite)
        db.session.commit()

class DirectModeratorInvite(db.Model):
    """Model for direct moderator invites from admins"""
    __tablename__ = 'direct_moderator_invites'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invite_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    role_permissions = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    company = db.relationship('Company')
    inviter = db.relationship('User', foreign_keys=[invited_by])
    
    def __init__(self, email, first_name, last_name, company_id, invited_by, role_permissions, message=None):
        self.email = email.lower()
        self.first_name = first_name
        self.last_name = last_name
        self.company_id = company_id
        self.invited_by = invited_by
        self.role_permissions = role_permissions
        self.message = message
        self.invite_token = self.generate_token()
        self.expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hours for direct invites
    
    @staticmethod
    def generate_token():
        """Generate a secure invite token"""
        return secrets.token_urlsafe(48)
    
    @property
    def is_expired(self):
        """Check if the invite has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the invite is valid (not expired and not used)"""
        return not self.is_expired and not self.is_used
    
    @property
    def full_name(self):
        """Get the full name of the invitee"""
        return f"{self.first_name} {self.last_name}"
    
    def mark_as_used(self):
        """Mark the invite as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired invites"""
        expired_invites = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for invite in expired_invites:
            db.session.delete(invite)
        db.session.commit() 