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
    
    # If no plans in database, create default plans
    if not subscription_plans:
        # Create default plans in the database
        try:
            free_plan = SubscriptionPlan(
                name="Free",
                price=0.00,
                billing_cycle="monthly",
                max_sales=50,
                max_users=2,
                feature_analytics=True,
                feature_export=False,
                feature_premium_tools=False
            )
            
            standard_plan = SubscriptionPlan(
                name="Standard",
                price=19.99,
                billing_cycle="monthly",
                max_sales=500,
                max_users=5,
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=False
            )
            
            premium_plan = SubscriptionPlan(
                name="Premium",
                price=49.99,
                billing_cycle="monthly",
                max_sales=0,  # Unlimited
                max_users=0,  # Unlimited
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=True
            )
            
            # Add to database
            db.session.add(free_plan)
            db.session.add(standard_plan)
            db.session.add(premium_plan)
            db.session.commit()
            
            # Retrieve the newly created plans
            subscription_plans = SubscriptionPlan.query.all()
        except Exception as e:
            # If there's an error creating plans, use hardcoded versions
            default_plans = [
                {
                    'name': 'Free',
                    'price': '0',
                    'features': [
                        'Sales tracking and management',
                        'Basic product and store management',
                        'Up to 50 sales entries per month',
                        'Up to 2 users per company',
                        'Basic analytics and reports',
                        'Community support'
                    ],
                    'recommended': False,
                    'button_text': 'Current Plan' if current_user.is_authenticated and current_user.company and current_user.company.is_free_plan else 'Get Started Free',
                    'plan_id': 1
                },
                {
                    'name': 'Standard',
                    'price': '19.99',
                    'features': [
                        'Everything in Free',
                        'Up to 500 sales entries per month',
                        'Up to 5 users per company',
                        'Data import/export (CSV)',
                        'Advanced analytics and reports',
                        'Email support',
                        'Data backup and restore'
                    ],
                    'recommended': True,
                    'button_text': 'Upgrade to Standard',
                    'plan_id': 2
                },
                {
                    'name': 'Premium',
                    'price': '49.99',
                    'features': [
                        'Everything in Standard',
                        'Unlimited sales entries',
                        'Unlimited users',
                        'Advanced data analytics',
                        'Custom reports and dashboards',
                        'Priority support',
                        'API access',
                        'Advanced security features',
                        'Custom integrations'
                    ],
                    'recommended': False,
                    'button_text': 'Upgrade to Premium',
                    'plan_id': 3
                }
            ]
            return render_template('pricing/index.html', plans=default_plans)
    
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
        elif plan.name == 'Free':
            button_text = 'Get Started Free'
        elif plan.name == 'Standard':
            button_text = 'Upgrade to Standard'
        elif plan.name == 'Premium':
            button_text = 'Upgrade to Premium'
        else:
            button_text = 'Contact Sales'
        
        # Build features list based on plan attributes and name
        features = []
        
        if plan.name == 'Free':
            features = [
                'Sales tracking and management',
                'Basic product and store management',
                f'Up to {plan.max_sales} sales entries per month',
                f'Up to {plan.max_users} users per company',
                'Basic analytics and reports',
                'Community support'
            ]
        elif plan.name == 'Standard':
            features = [
                'Everything in Free',
                f'Up to {plan.max_sales} sales entries per month',
                f'Up to {plan.max_users} users per company',
                'Data import/export (CSV)',
                'Advanced analytics and reports',
                'Email support',
                'Data backup and restore'
            ]
        elif plan.name == 'Premium':
            features = [
                'Everything in Standard',
                'Unlimited sales entries',
                'Unlimited users',
                'Advanced data analytics',
                'Custom reports and dashboards',
                'Priority support',
                'API access',
                'Advanced security features',
                'Custom integrations'
            ]
        else:
            # Fallback for other plans
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
        
        default_plans.append({
            'name': plan.name,
            'price': f'{plan.price:.2f}' if plan.price > 0 else '0',
            'features': features,
            'recommended': plan.name == 'Standard',
            'button_text': button_text,
            'plan_id': plan.id
        })
    
    return render_template('pricing/index.html', plans=default_plans)

@pricing.route('/upgrade/<int:plan_id>', methods=['GET'])
@login_required
def upgrade(plan_id):
    """Redirect to payment page for subscription upgrade"""
    # Verify plan exists
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Enterprise plan requires contacting sales
    if plan.name == 'Enterprise':
        flash('Please contact our sales team to set up an Enterprise plan.', 'info')
        return redirect(url_for('contact.index'))
    
    # If the user already has this plan, no need to upgrade
    if current_user.company and current_user.company.subscription_plan_id == plan_id:
        flash('You are already subscribed to this plan.', 'info')
        return redirect(url_for('dashboard.index'))
    
    # Redirect to payment checkout for the selected plan
    return redirect(url_for('payment.checkout', plan_id=plan_id))

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