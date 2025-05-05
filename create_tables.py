from app import create_app, db
from app.models import User, Product, ProductCategory, Company, Tool, Sale, SaleItem, Store, BlogPost, Question, Answer, RoleWebsite, RoleCompany, CompanySchema

# Create app with the development configuration
app = create_app('development')

# Create an application context
with app.app_context():
    # Create all tables
    db.create_all()
    
    # Initialize default roles
    default_website_roles = ['admin', 'moderator', 'subscriber', 'viewer']
    default_company_roles = ['admin', 'moderator']
    
    # Create website roles
    for role_name in default_website_roles:
        if not RoleWebsite.query.get(role_name):
            role = RoleWebsite(role_name=role_name)
            db.session.add(role)
    
    # Create company roles
    for role_name in default_company_roles:
        if not RoleCompany.query.get(role_name):
            role = RoleCompany(role_name=role_name)
            db.session.add(role)
    
    # Commit the changes
    db.session.commit()
    
    print("All database tables and default roles have been created successfully!") 