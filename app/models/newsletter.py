from app import db
from datetime import datetime

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    unsubscribed_at = db.Column(db.DateTime)
    source = db.Column(db.String(50), default='admin')  # admin, api, import, etc.
    
    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split('@')[0]
    
    def unsubscribe(self):
        """Unsubscribe user from newsletter"""
        self.is_active = False
        self.unsubscribed_at = datetime.utcnow()
        db.session.commit()
    
    def resubscribe(self):
        """Resubscribe user to newsletter"""
        self.is_active = True
        self.unsubscribed_at = None
        db.session.commit()

class NewsletterCampaign(db.Model):
    __tablename__ = 'newsletter_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft', nullable=False)  # draft, sending, sent, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Statistics
    total_recipients = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    opens = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    
    # Relationships
    created_by = db.relationship('User', backref='newsletter_campaigns')
    
    def __repr__(self):
        return f'<NewsletterCampaign {self.title}>'
    
    @property
    def success_rate(self):
        if self.total_recipients == 0:
            return 0
        return round((self.emails_sent / self.total_recipients) * 100, 1)

class NewsletterTemplate(db.Model):
    __tablename__ = 'newsletter_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    html_template = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<NewsletterTemplate {self.name}>' 