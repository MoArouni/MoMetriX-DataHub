from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.subscription import CompanySubscription, SubscriptionPlan
from app.models.company import Company
from app.utils.decorators import company_admin_required
from app.utils.stripe_utils import (
    create_stripe_checkout_session, 
    cancel_subscription, 
    update_subscription_plan, 
    get_subscription_details,
    handle_webhook_event
)
from datetime import datetime
from dateutil.relativedelta import relativedelta

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

@payment_bp.route('/checkout/<int:plan_id>', methods=['GET', 'POST'])
@login_required
@company_admin_required
def checkout(plan_id):
    """Create a checkout session for subscription purchase"""
    # Verify the requested plan exists
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    company_id = current_user.company.id
    
    # For free plans, skip Stripe checkout
    if plan.price <= 0:
        # Update company's subscription plan
        current_user.company.subscription_plan_id = plan.id
        
        # Create or update subscription record
        subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
        if not subscription:
            subscription = CompanySubscription(
                company_id=company_id,
                plan_id=plan.id,
                status='active',
                current_period_start=datetime.utcnow(),
                current_period_end=None  # Free plan has no end
            )
            db.session.add(subscription)
        else:
            subscription.plan_id = plan.id
            subscription.status = 'active'
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = None
            subscription.payment_method = None
            subscription.payment_provider_id = None
        
        db.session.commit()
        flash(f'Your company has been successfully subscribed to the {plan.name} plan!', 'success')
        return redirect(url_for('dashboard.index'))
    
    # For paid plans, create a Stripe checkout session
    try:
        session = create_stripe_checkout_session(
            customer_email=current_user.email,
            plan_id=plan_id,
            company_id=company_id
        )
        
        # Redirect to Stripe's checkout page
        return render_template(
            'payment/checkout.html', 
            checkout_session_id=session.id,
            stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'],
            plan=plan
        )
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {str(e)}")
        flash('An error occurred while processing your payment. Please try again.', 'error')
        return redirect(url_for('pricing.index'))

@payment_bp.route('/success')
@login_required
def success():
    """Handle successful payment"""
    plan_id = request.args.get('plan_id')
    company_id = request.args.get('company_id')
    
    if not plan_id or not company_id:
        flash('Invalid request parameters.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Verify the plan exists
    plan = SubscriptionPlan.query.get_or_404(int(plan_id))
    company = Company.query.get_or_404(int(company_id))
    
    # Only company admins or site admins can update subscription
    if not current_user.is_admin and (current_user.company_id != int(company_id) or current_user.role_company != 'admin'):
        flash('You do not have permission to update this company\'s subscription.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Update company's subscription plan
    company.subscription_plan_id = plan.id
    
    # Calculate end date based on billing cycle
    end_date = None
    if plan.billing_cycle == 'monthly':
        end_date = datetime.utcnow() + relativedelta(months=1)
    elif plan.billing_cycle == 'yearly':
        end_date = datetime.utcnow() + relativedelta(years=1)
    
    # Create or update subscription record
    # In a real implementation, you'd get this data from Stripe's webhook
    subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
    if not subscription:
        subscription = CompanySubscription(
            company_id=int(company_id),
            plan_id=int(plan_id),
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=end_date,
            payment_method='credit_card',
            payment_provider_id='stripe_payment'  # In a real implementation, this would be the Stripe subscription ID
        )
        db.session.add(subscription)
    else:
        subscription.plan_id = int(plan_id)
        subscription.status = 'active'
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = end_date
        subscription.payment_method = 'credit_card'
        subscription.payment_provider_id = 'stripe_payment'  # In a real implementation, this would be the Stripe subscription ID
    
    db.session.commit()
    
    return render_template('payment/success.html', plan=plan)

@payment_bp.route('/cancel')
@login_required
def cancel():
    """Handle cancelled payment"""
    flash('Payment cancelled. Your subscription has not been changed.', 'info')
    return redirect(url_for('pricing.index'))

@payment_bp.route('/manage')
@login_required
@company_admin_required
def manage():
    """Manage existing subscription"""
    company_id = current_user.company.id
    subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
    
    if not subscription:
        flash('You don\'t have an active subscription.', 'info')
        return redirect(url_for('pricing.index'))
    
    # In a real implementation, you'd get additional subscription details from Stripe
    # if subscription.payment_provider_id:
    #     stripe_subscription = get_subscription_details(subscription.payment_provider_id)
    # else:
    #     stripe_subscription = None
    
    plans = SubscriptionPlan.query.all()
    
    return render_template(
        'payment/manage.html', 
        subscription=subscription,
        plans=plans
    )

@payment_bp.route('/cancel-subscription', methods=['POST'])
@login_required
@company_admin_required
def cancel_subscription_route():
    """Cancel existing subscription"""
    company_id = current_user.company.id
    subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
    
    if not subscription:
        flash('You don\'t have an active subscription to cancel.', 'info')
        return redirect(url_for('pricing.index'))
    
    # In a real implementation, you'd cancel the subscription in Stripe
    # if subscription.payment_provider_id:
    #     try:
    #         canceled = cancel_subscription(subscription.payment_provider_id)
    #     except Exception as e:
    #         current_app.logger.error(f"Error canceling subscription: {str(e)}")
    #         flash('An error occurred while canceling your subscription. Please try again.', 'error')
    #         return redirect(url_for('payment.manage'))
    
    # Update subscription status
    subscription.status = 'canceled'
    db.session.commit()
    
    flash('Your subscription has been canceled. You will continue to have access until the end of your billing period.', 'success')
    return redirect(url_for('payment.manage'))

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    signature = request.headers.get('Stripe-Signature')
    
    try:
        event = handle_webhook_event(payload, signature)
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        # Payment was successful, update subscription
        session = event['data']['object']
        customer_email = session.get('customer_email')
        metadata = session.get('metadata', {})
        plan_id = metadata.get('plan_id')
        company_id = metadata.get('company_id')
        
        if plan_id and company_id:
            # Update the company's subscription
            company = Company.query.get(int(company_id))
            plan = SubscriptionPlan.query.get(int(plan_id))
            
            if company and plan:
                company.subscription_plan_id = plan.id
                
                # Calculate end date based on billing cycle
                end_date = None
                if plan.billing_cycle == 'monthly':
                    end_date = datetime.utcnow() + relativedelta(months=1)
                elif plan.billing_cycle == 'yearly':
                    end_date = datetime.utcnow() + relativedelta(years=1)
                
                # Create or update subscription record
                subscription = CompanySubscription.query.filter_by(company_id=company_id).first()
                if not subscription:
                    subscription = CompanySubscription(
                        company_id=int(company_id),
                        plan_id=int(plan_id),
                        status='active',
                        current_period_start=datetime.utcnow(),
                        current_period_end=end_date,
                        payment_method='credit_card',
                        payment_provider_id=session.get('subscription')  # Store Stripe subscription ID
                    )
                    db.session.add(subscription)
                else:
                    subscription.plan_id = int(plan_id)
                    subscription.status = 'active'
                    subscription.current_period_start = datetime.utcnow()
                    subscription.current_period_end = end_date
                    subscription.payment_method = 'credit_card'
                    subscription.payment_provider_id = session.get('subscription')  # Store Stripe subscription ID
                
                db.session.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        # Subscription was canceled or has expired
        subscription_object = event['data']['object']
        subscription_id = subscription_object.get('id')
        
        # Find the CompanySubscription with this payment_provider_id
        company_subscription = CompanySubscription.query.filter_by(payment_provider_id=subscription_id).first()
        
        if company_subscription:
            # Update status to canceled
            company_subscription.status = 'canceled'
            db.session.commit()
    
    # Return a 200 response to acknowledge receipt of the event
    return jsonify({'status': 'success'}) 