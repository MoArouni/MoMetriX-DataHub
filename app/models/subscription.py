from datetime import datetime
from app import db

class SubscriptionPlan(db.Model):
    """Subscription plans available in the system"""
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly, yearly
    max_sales = db.Column(db.Integer, default=100)
    max_users = db.Column(db.Integer, default=3)
    feature_analytics = db.Column(db.Boolean, default=True)
    feature_export = db.Column(db.Boolean, default=True)
    feature_premium_tools = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with companies
    companies = db.relationship('Company', backref='subscription_plan', lazy='dynamic')
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name} - ${self.price}>'

class CompanySubscription(db.Model):
    """Tracks company subscription information"""
    __tablename__ = 'company_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, canceled, past_due
    current_period_start = db.Column(db.DateTime, default=datetime.utcnow)
    current_period_end = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_provider_id = db.Column(db.String(100), nullable=True)  # ID from payment provider
    sales_count = db.Column(db.Integer, default=0)
    user_count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='subscription_details', uselist=False)
    plan = db.relationship('SubscriptionPlan')
    
    def __repr__(self):
        return f'<CompanySubscription {self.company_id} - {self.plan.name if self.plan else "No Plan"}>'
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def can_add_sale(self):
        return self.is_active and (self.sales_count < self.plan.max_sales)
    
    @property
    def can_add_user(self):
        return self.is_active and (self.user_count < self.plan.max_users)
        
    @property
    def sales_usage_percent(self):
        if self.plan.max_sales > 0:
            return (self.sales_count / self.plan.max_sales) * 100
        return 0
    
    @property
    def user_usage_percent(self):
        if self.plan.max_users > 0:
            return (self.user_count / self.plan.max_users) * 100
        return 0