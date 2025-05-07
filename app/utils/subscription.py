from flask import flash, redirect, url_for
from flask_login import current_user
from app.models.subscription import CompanySubscription, SubscriptionPlan
from app import db
from datetime import datetime

def check_feature_access(feature_name):
    """
    Check if a user has access to a specific feature based on their subscription
    
    Args:
        feature_name: Feature name to check (e.g., 'premium_tools', 'export', etc.)
        
    Returns:
        bool: True if user has access, False otherwise
    """
    if not current_user.is_authenticated or not current_user.company:
        return False
        
    subscription = CompanySubscription.query.filter_by(company_id=current_user.company.id).first()
    if not subscription or not subscription.is_active:
        return False
        
    plan = subscription.plan
    
    # Check for specific features
    if feature_name == 'premium_tools':
        return plan.feature_premium_tools
    elif feature_name == 'export':
        return plan.feature_export
    elif feature_name == 'analytics':
        return plan.feature_analytics
    
    # Default to False for unknown features
    return False

def check_sales_limit(redirect_if_limited=True):
    """
    Check if a company has reached its sales limit
    
    Args:
        redirect_if_limited: Whether to redirect to pricing page if limit reached
        
    Returns:
        tuple: (bool, CompanySubscription) 
        - bool is True if limit not reached (can add sale), False otherwise
        - CompanySubscription object
    """
    if not current_user.is_authenticated or not current_user.company:
        return False, None
        
    subscription = CompanySubscription.query.filter_by(company_id=current_user.company.id).first()
    
    # If no subscription, create a free plan subscription
    if not subscription:
        free_plan = SubscriptionPlan.query.filter_by(name='Free').first()
        if not free_plan:
            # Create default free plan if none exists
            free_plan = SubscriptionPlan(
                name='Free',
                price=0.0,
                max_sales=100,
                max_users=3,
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=False
            )
            db.session.add(free_plan)
            db.session.flush()
            
        subscription = CompanySubscription(
            company_id=current_user.company.id,
            plan_id=free_plan.id,
            status='active',
            current_period_start=datetime.utcnow()
        )
        db.session.add(subscription)
        db.session.commit()
    
    can_add = subscription.can_add_sale
    
    if not can_add and redirect_if_limited:
        flash('You have reached your sales limit. Please upgrade your plan to add more sales.', 'warning')
        return False, subscription
        
    return can_add, subscription

def check_user_limit(redirect_if_limited=True):
    """
    Check if a company has reached its user limit
    
    Args:
        redirect_if_limited: Whether to redirect to pricing page if limit reached
        
    Returns:
        tuple: (bool, CompanySubscription) 
        - bool is True if limit not reached (can add user), False otherwise
        - CompanySubscription object
    """
    if not current_user.is_authenticated or not current_user.company:
        return False, None
        
    subscription = CompanySubscription.query.filter_by(company_id=current_user.company.id).first()
    
    # If no subscription, create a free plan subscription
    if not subscription:
        free_plan = SubscriptionPlan.query.filter_by(name='Free').first()
        if not free_plan:
            # Create default free plan if none exists
            free_plan = SubscriptionPlan(
                name='Free',
                price=0.0,
                max_sales=100,
                max_users=3,
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=False
            )
            db.session.add(free_plan)
            db.session.flush()
            
        subscription = CompanySubscription(
            company_id=current_user.company.id,
            plan_id=free_plan.id,
            status='active',
            current_period_start=datetime.utcnow()
        )
        db.session.add(subscription)
        db.session.commit()
    
    can_add = subscription.can_add_user
    
    if not can_add and redirect_if_limited:
        flash('You have reached your user limit. Please upgrade your plan to add more users.', 'warning')
        return False, subscription
        
    return can_add, subscription

def update_user_count(company_id):
    """
    Update the user count for a company's subscription
    
    Args:
        company_id: ID of the company to update
    """
    from app.models.user import User
    
    subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
    if subscription:
        # Count users in this company
        user_count = User.query.filter_by(company_id=company_id).count()
        subscription.user_count = user_count
        db.session.commit()
        
    return subscription 