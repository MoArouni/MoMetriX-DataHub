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
                max_sales=100,
                max_users=3,
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=False
            )
            
            pro_plan = SubscriptionPlan(
                name="Pro",
                price=29.00,
                billing_cycle="monthly",
                max_sales=1000,
                max_users=10,
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=True
            )
            
            enterprise_plan = SubscriptionPlan(
                name="Enterprise",
                price=99.00,
                billing_cycle="monthly",
                max_sales=0,  # Unlimited
                max_users=0,  # Unlimited
                feature_analytics=True,
                feature_export=True,
                feature_premium_tools=True
            )
            
            # Add to database
            db.session.add(free_plan)
            db.session.add(pro_plan)
            db.session.add(enterprise_plan)
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
                        'Basic data analysis',
                        'Limited API access',
                        'Community support',
                        'Basic visualization tools',
                        'Up to 100 sales entries',
                        'Up to 3 users per company'
                    ],
                    'recommended': False,
                    'button_text': 'Current Plan' if current_user.is_authenticated and current_user.company and current_user.company.is_free_plan else 'Get Started',
                    'plan_id': 1  # Add plan_id for template
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
                    'button_text': 'Upgrade Now',
                    'plan_id': 2  # Add plan_id for template
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
                    'button_text': 'Contact Sales',
                    'plan_id': 3  # Add plan_id for template
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