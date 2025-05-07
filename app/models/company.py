from datetime import datetime
from app import db

class Company(db.Model):
    """Company model that users belong to"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), unique=True, nullable=False)
    company_email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin relationship - separate from the members backref
    admin = db.relationship('User', foreign_keys=[admin_id], backref='administered_company', uselist=False)
    
    # Relationships defined in other models
    # employees - defined in User model
    # sales - defined in Sales model
    # subscription_plan - defined in SubscriptionPlan model
    # subscription_details - defined in CompanySubscription model
    
    def __repr__(self):
        return f'<Company {self.company_name}>'
    
    @property
    def current_subscription(self):
        """Return the current subscription details"""
        from app.models.subscription import CompanySubscription
        return CompanySubscription.query.filter_by(company_id=self.id).first()
    
    @property
    def has_active_subscription(self):
        """Check if company has an active subscription"""
        sub = self.current_subscription
        return sub is not None and sub.is_active
    
    @property
    def can_add_sale(self):
        """Check if company can add more sales based on subscription"""
        sub = self.current_subscription
        return sub is not None and sub.can_add_sale
    
    @property 
    def can_add_user(self):
        """Check if company can add more users based on subscription"""
        sub = self.current_subscription
        return sub is not None and sub.can_add_user
    
    @property
    def is_free_plan(self):
        """Check if company is on free plan"""
        if not self.subscription_plan_id:
            return True
        from app.models.subscription import SubscriptionPlan
        plan = SubscriptionPlan.query.get(self.subscription_plan_id)
        return plan is not None and plan.name == 'Free' 