from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models.subscription import SubscriptionPlan, CompanySubscription
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

pricing = Blueprint('pricing', __name__)

@pricing.route('/pricing')
def index():
    """Pricing page with subscription plans"""
    # Get all available subscription plans
    subscription_plans = SubscriptionPlan.query.all()
    
    # If no plans in database, use default plans
    if not subscription_plans:
        default_plans = [
            {
                'name': 'Free',
                'price': '0',
                'features': [
                    'Basic data analysis',
                    'Limited API access',
                    'Community support',
                    'Basic visualization tools',
                    'Up to 100 sales entries',
                    'Up to 3 users per company'
                ],
                'recommended': False,
                'button_text': 'Current Plan' if current_user.is_authenticated and current_user.company and current_user.company.is_free_plan else 'Get Started'
            },
            {
                'name': 'Pro',
                'price': '29',
                'features': [
                    'Advanced data analysis',
                    'Full API access',
                    'Priority support',
                    'Advanced visualization tools',
                    'Custom reports',
                    'Team collaboration',
                    'Up to 1,000 sales entries',
                    'Up to 10 users per company'
                ],
                'recommended': True,
                'button_text': 'Upgrade Now'
            },
            {
                'name': 'Enterprise',
                'price': '99',
                'features': [
                    'Everything in Pro',
                    'Dedicated support',
                    'Custom solutions',
                    'SLA guarantee',
                    'Advanced security',
                    'Training sessions',
                    'Unlimited sales entries',
                    'Unlimited users'
                ],
                'recommended': False,
                'button_text': 'Contact Sales'
            }
        ]
    else:
        # Convert database plans to template format
        default_plans = []
        for plan in subscription_plans:
            # Determine if this is the current plan for the user
            is_current = False
            if current_user.is_authenticated and current_user.company:
                if current_user.company.subscription_plan_id == plan.id:
                    is_current = True
            
            # Set appropriate button text
            if is_current:
                button_text = 'Current Plan'
            elif plan.name == 'Enterprise':
                button_text = 'Contact Sales'
            else:
                button_text = 'Upgrade Now'
            
            # Build features list based on plan attributes
            features = []
            
            if plan.max_sales == 0:
                features.append('Unlimited sales entries')
            else:
                features.append(f'Up to {plan.max_sales:,} sales entries')
                
            if plan.max_users == 0:
                features.append('Unlimited users')
            else:
                features.append(f'Up to {plan.max_users} users per company')
                
            if plan.feature_analytics:
                features.append('Data analysis tools')
                
            if plan.feature_export:
                features.append('Data export capabilities')
                
            if plan.feature_premium_tools:
                features.append('Premium analysis tools')
                
            # Other features based on plan name
            if plan.name == 'Pro' or plan.name == 'Enterprise':
                features.append('Priority support')
                features.append('Advanced visualization')
                
            if plan.name == 'Enterprise':
                features.append('Dedicated support')
                features.append('Custom solutions')
                features.append('SLA guarantee')
            
            default_plans.append({
                'name': plan.name,
                'price': str(int(plan.price)),
                'features': features,
                'recommended': plan.name == 'Pro',
                'button_text': button_text,
                'plan_id': plan.id
            })
    
    return render_template('pricing/index.html', plans=default_plans)

@pricing.route('/pricing/upgrade/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def upgrade(plan_id):
    """Handle plan upgrade/subscription process"""
    # Verify plan exists
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Enterprise plan requires contacting sales
    if plan.name == 'Enterprise':
        flash('Please contact our sales team to set up an Enterprise plan.', 'info')
        return redirect(url_for('contact.index'))
    
    # If free plan, just update company's subscription plan
    if plan.name == 'Free':
        if current_user.company:
            # Update company's plan
            current_user.company.subscription_plan_id = plan.id
            
            # Create or update CompanySubscription record
            subscription = CompanySubscription.query.filter_by(company_id=current_user.company.id).first()
            if not subscription:
                subscription = CompanySubscription(
                    company_id=current_user.company.id,
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
            
            db.session.commit()
            flash('Your company has been successfully subscribed to the Free plan!', 'success')
            return redirect(url_for('dashboard.index'))
    
    # For paid plans, redirect to payment page (this will be implemented in next step)
    # For now, just simulate a successful payment
    if current_user.company:
        # Update company's plan
        current_user.company.subscription_plan_id = plan.id
        
        # Calculate end date based on billing cycle
        end_date = None
        if plan.billing_cycle == 'monthly':
            end_date = datetime.utcnow() + relativedelta(months=1)
        elif plan.billing_cycle == 'yearly':
            end_date = datetime.utcnow() + relativedelta(years=1)
        
        # Create or update CompanySubscription record
        subscription = CompanySubscription.query.filter_by(company_id=current_user.company.id).first()
        if not subscription:
            subscription = CompanySubscription(
                company_id=current_user.company.id,
                plan_id=plan.id,
                status='active',
                current_period_start=datetime.utcnow(),
                current_period_end=end_date,
                payment_method='credit_card',  # Placeholder
                payment_provider_id='simulated_payment'  # Placeholder
            )
            db.session.add(subscription)
        else:
            subscription.plan_id = plan.id
            subscription.status = 'active'
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = end_date
            subscription.payment_method = 'credit_card'  # Placeholder
            subscription.payment_provider_id = 'simulated_payment'  # Placeholder
        
        db.session.commit()
        flash(f'Your company has been successfully subscribed to the {plan.name} plan!', 'success')
        return redirect(url_for('dashboard.index'))
    
    flash('You need to create a company before subscribing to a plan.', 'warning')
    return redirect(url_for('dashboard.create_company'))

@pricing.route('/api/subscription/usage')
@login_required
def subscription_usage():
    """API endpoint to get subscription usage information"""
    if not current_user.company:
        return jsonify({
            'error': 'No company associated with this user'
        }), 400
    
    subscription = CompanySubscription.query.filter_by(company_id=current_user.company.id).first()
    if not subscription:
        return jsonify({
            'error': 'No subscription found for this company'
        }), 404
    
    return jsonify({
        'plan_name': subscription.plan.name,
        'status': subscription.status,
        'sales': {
            'count': subscription.sales_count,
            'limit': subscription.plan.max_sales,
            'percentage': subscription.sales_usage_percent
        },
        'users': {
            'count': subscription.user_count,
            'limit': subscription.plan.max_users,
            'percentage': subscription.user_usage_percent
        },
        'period': {
            'start': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            'end': subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }
    })