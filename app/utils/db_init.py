from app import db
from app.models.roles import RoleWebsite, RoleCompany

def init_roles():
    """Initialize default roles in the database"""
    try:
        # Create website roles if they don't exist
        default_website_roles = ['admin', 'moderator', 'subscriber']
        for role_name in default_website_roles:
            if not RoleWebsite.query.get(role_name):
                role = RoleWebsite(role_name=role_name)
                db.session.add(role)
        
        # Create company roles if they don't exist
        default_company_roles = ['admin', 'moderator']
        for role_name in default_company_roles:
            if not RoleCompany.query.get(role_name):
                role = RoleCompany(role_name=role_name)
                db.session.add(role)
        
        db.session.commit()
    except Exception as e:
        # If tables don't exist yet, just pass
        db.session.rollback()
        pass

def initialize_database():
    """Initialize the database with required default data"""
    init_roles()
    # Add other initialization functions here as needed
    print("Database initialization complete.")

if __name__ == "__main__":
    # This allows running this script directly
    from app import create_app
    app = create_app()
    with app.app_context():
        initialize_database() 