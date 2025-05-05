#!/usr/bin/env python3
from app import create_app, db
from app.models import User, Company, Tool, BlogPost, Question, Answer, RoleWebsite, RoleCompany
from app.models import Product, ProductCategory, Sale, SaleItem, Store, CompanySchema, MailingList
import os
import shutil

def reset_database():
    """Reset and recreate the entire database"""
    print("Starting database reset...")
    
    # Get app context - use development config for testing
    app = create_app('development')
    
    with app.app_context():
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Check if an SQLite database file exists and delete it
        sqlite_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if sqlite_path.startswith('sqlite:///'):
            # Extract the path part
            db_path = sqlite_path.replace('sqlite:///', '')
            # Make relative path absolute
            if not os.path.isabs(db_path):
                db_path = os.path.join(app.root_path, '..', db_path)
            
            # Delete the file if it exists
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"Deleted existing SQLite database file: {db_path}")
                except OSError as e:
                    print(f"Error removing SQLite file: {e}")
        
        # Create all tables
        print("Creating all database tables...")
        db.create_all()
        
        # Initialize website roles
        default_website_roles = ['admin', 'moderator', 'subscriber', 'viewer']
        for role_name in default_website_roles:
            role = RoleWebsite(role_name=role_name)
            db.session.add(role)
        
        # Initialize company roles
        default_company_roles = ['admin', 'moderator']
        for role_name in default_company_roles:
            role = RoleCompany(role_name=role_name)
            db.session.add(role)
        
        # Commit the changes
        db.session.commit()
        
        print("Database reset complete. All tables have been recreated.")
        print("Default website roles created:", default_website_roles)
        print("Default company roles created:", default_company_roles)

if __name__ == "__main__":
    reset_database() 