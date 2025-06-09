import stripe
from flask import current_app, url_for
from app.models.subscription import SubscriptionPlan
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

def initialize_stripe():
    """Initialize Stripe with API key from config"""
    try:
        if 'STRIPE_SECRET_KEY' not in current_app.config:
            current_app.logger.error("STRIPE_SECRET_KEY not found in app configuration")
            return None
            
        if not current_app.config['STRIPE_SECRET_KEY'] or current_app.config['STRIPE_SECRET_KEY'] == 'sk_test_your_test_key':
            current_app.logger.warning("Using default test Stripe key. Set STRIPE_SECRET_KEY environment variable for production.")
            # Return None in production, but for development/testing, use test key
            if current_app.config.get('ENV') != 'development' and not current_app.config.get('TESTING'):
                return None
            
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        return stripe
    except Exception as e:
        current_app.logger.error(f"Failed to initialize Stripe: {str(e)}")
        return None

def create_stripe_checkout_session(customer_email, plan_id, company_id):
    """
    Create a Stripe checkout session for subscription purchase
    
    Args:
        customer_email: Customer's email address
        plan_id: ID of the plan being purchased
        company_id: ID of the company making the purchase
        
    Returns:
        The Stripe checkout session
    """
    stripe_instance = initialize_stripe()
    if not stripe_instance:
        current_app.logger.error("Cannot create checkout session: Stripe not initialized")
        raise ValueError("Stripe payment service is not configured properly. Please contact support.")
    
    # Get the subscription plan details
    plan = SubscriptionPlan.query.get(plan_id)
    if not plan:
        raise ValueError(f"Subscription plan with ID {plan_id} not found")
        
    # Skip Stripe for free plans
    if plan.price <= 0:
        return None
    
    try:
        # Create a success and cancel URL
        success_url = url_for('payment.success', plan_id=plan_id, company_id=company_id, _external=True)
        cancel_url = url_for('payment.cancel', _external=True)
        
        # Convert to cents for Stripe
        price_in_cents = int(plan.price * 100)
        
        # Create the checkout session
        session = stripe_instance.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{plan.name} Plan',
                        'description': f'Subscription to {plan.name} plan with access to premium features',
                    },
                    'unit_amount': price_in_cents,
                    'recurring': {
                        'interval': 'month' if plan.billing_cycle == 'monthly' else 'year',
                        'interval_count': 1,
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
            metadata={
                'plan_id': plan_id,
                'company_id': company_id,
                'plan_name': plan.name
            }
        )
        
        return session
    except Exception as e:
        current_app.logger.error(f"Error creating Stripe checkout session: {str(e)}")
        raise ValueError(f"Failed to create checkout session: {str(e)}")

def cancel_subscription(subscription_id):
    """
    Cancel a Stripe subscription
    
    Args:
        subscription_id: The Stripe subscription ID to cancel
        
    Returns:
        The canceled subscription object
    """
    stripe = initialize_stripe()
    
    try:
        # Cancel at period end rather than immediately
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return subscription
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        current_app.logger.error(f"Stripe error when canceling subscription: {str(e)}")
        raise e
        
def update_subscription_plan(subscription_id, new_plan_id):
    """
    Change a subscription to a new plan
    
    Args:
        subscription_id: The Stripe subscription ID to update
        new_plan_id: ID of the new plan
        
    Returns:
        The updated subscription object
    """
    stripe = initialize_stripe()
    
    # Get the new plan details
    plan = SubscriptionPlan.query.get(new_plan_id)
    if not plan:
        raise ValueError(f"Subscription plan with ID {new_plan_id} not found")
    
    # Convert to cents for Stripe
    price_in_cents = int(plan.price * 100)
    
    try:
        # Get current subscription to find the item ID
        current_subscription = stripe.Subscription.retrieve(subscription_id)
        subscription_item_id = current_subscription['items']['data'][0]['id']
        
        # Update the subscription
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{
                'id': subscription_item_id,
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{plan.name} Plan',
                    },
                    'unit_amount': price_in_cents,
                    'recurring': {
                        'interval': 'month' if plan.billing_cycle == 'monthly' else 'year',
                        'interval_count': 1,
                    },
                },
            }],
            metadata={
                'plan_id': new_plan_id,
                'plan_name': plan.name
            }
        )
        
        return updated_subscription
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        current_app.logger.error(f"Stripe error when updating subscription plan: {str(e)}")
        raise e

def get_subscription_details(subscription_id):
    """
    Get details of a Stripe subscription
    
    Args:
        subscription_id: The Stripe subscription ID
        
    Returns:
        The subscription object with details
    """
    stripe = initialize_stripe()
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        current_app.logger.error(f"Stripe error when retrieving subscription: {str(e)}")
        raise e

def handle_webhook_event(payload, signature):
    """
    Handle Stripe webhook events
    
    Args:
        payload: The request body
        signature: The Stripe signature header
        
    Returns:
        The parsed Stripe event
    """
    stripe = initialize_stripe()
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        return event
    except ValueError as e:
        # Invalid payload
        current_app.logger.error(f"Invalid Stripe webhook payload: {str(e)}")
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        current_app.logger.error(f"Invalid Stripe webhook signature: {str(e)}")
        raise e 