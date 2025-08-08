"""
Script to create initial subscription plans in the database
"""
from app import create_app, db
from app.models.subscription import SubscriptionPlan, CompanySubscription
from app.models.company import Company
from app.models.user import User

def create_subscription_plans():
    # Create application context
    app = create_app()
    with app.app_context():
        # Check if plans already exist
        existing_plans = SubscriptionPlan.query.count()
        if existing_plans > 0:
            print("Subscription plans already exist. Exiting.")
            return
            
        # Create plans
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
            price=4.99,
            billing_cycle="monthly",
            max_sales=500,
            max_users=5,
            feature_analytics=True,
            feature_export=True,
            feature_premium_tools=False
        )
        
        premium_plan = SubscriptionPlan(
            name="Premium",
            price=9.99,
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
        
        print(f"Created plans: {free_plan.name}, {standard_plan.name}, {premium_plan.name}")
        
        # Set all existing companies to Free plan
        free_plan = SubscriptionPlan.query.filter_by(name="Free").first()
        if free_plan:
            companies = Company.query.all()
            for company in companies:
                company.subscription_plan_id = free_plan.id
                
                # Create subscription record
                subscription = CompanySubscription(
                    company_id=company.id,
                    plan_id=free_plan.id,
                    status="active"
                )
                
                # Count users in this company
                user_count = User.query.filter_by(company_id=company.id).count()
                subscription.user_count = user_count
                
                db.session.add(subscription)
                
            db.session.commit()
            print(f"Updated {len(companies)} existing companies to Free plan")
        
        print("Done!")

if __name__ == "__main__":
    create_subscription_plans() 