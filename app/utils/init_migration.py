from app import db, create_app
from app.models.roles import RoleWebsite, RoleCompany
from app.models.user import User
from app.models.company import Company
from app.models.blog import BlogPost
from app.models.qa import Question, Answer
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.store import Store
from app.models.sales import Sale, SaleItem
from app.models.schema import CompanySchema

def create_roles():
    """Create default roles in the database"""
    print("Creating default roles...")
    
    # Website roles
    website_roles = [
        RoleWebsite(role_name='admin'),
        RoleWebsite(role_name='moderator'),
        RoleWebsite(role_name='subscriber'),
        RoleWebsite(role_name='viewer')
    ]
    db.session.add_all(website_roles)
    
    # Company roles
    company_roles = [
        RoleCompany(role_name='admin'),
        RoleCompany(role_name='moderator')
    ]
    db.session.add_all(company_roles)
    
    db.session.commit()
    print("Default roles created successfully.")

def create_schema():
    """Create the initial database schema"""
    print("Creating database schema...")
    
    # Create all tables
    db.create_all()
    print("Database schema created successfully.")

def init_database():
    """Initialize the database with schema and default data"""
    # Create schema first
    create_schema()
    
    # Then populate with default data
    create_roles()
    
    print("Database initialization complete.")

if __name__ == "__main__":
    # This allows running this script directly
    app = create_app()
    with app.app_context():
        init_database() 