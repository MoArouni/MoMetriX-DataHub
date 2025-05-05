import sys
from app import create_app, db
from app.models.admin import Admin

def create_admin_user():
    """Create an admin user interactively"""
    
    print("=== Create Admin User ===")
    
    # Get admin credentials
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    
    # Get password using regular input instead of getpass
    print("Note: Password will be visible when typing")
    password = input("Enter admin password: ")
    confirm_password = input("Confirm admin password: ")
    
    # Validate input
    if not username or not email or not password:
        print("Error: All fields are required")
        return False
        
    if password != confirm_password:
        print("Error: Passwords do not match")
        return False
    
    # Create app context
    app = create_app('development')
    with app.app_context():
        # Check if admin exists
        if Admin.query.filter_by(username=username).first() or Admin.query.filter_by(email=email).first():
            print("Error: An admin with this username or email already exists")
            return False
            
        # Create admin user
        admin = Admin(username=username, email=email)
        admin.password = password
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully!")
        print(f"You can now login at /admin/login")
        return True
        
if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1) 