import click
from flask.cli import with_appcontext
from app import db
from app.utils.db_init import initialize_database

def register_commands(app):
    """Register Flask CLI commands"""
    
    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Initialize the database with schema and default data."""
        click.echo('Initializing the database...')
        
        # Drop all tables first if they exist
        db.drop_all()
        click.echo('Dropped existing tables.')
        
        # Create tables
        db.create_all()
        click.echo('Created new tables.')
        
        # Initialize with default data
        initialize_database()
        click.echo('Database initialization complete.')
    
    @app.cli.command('reset-roles')
    @with_appcontext
    def reset_roles():
        """Reset roles without affecting other data."""
        from app.models.roles import RoleWebsite, RoleCompany
        from app.utils.db_init import init_roles
        
        click.echo('Resetting roles...')
        # Delete existing roles
        RoleWebsite.query.delete()
        RoleCompany.query.delete()
        db.session.commit()
        
        # Create new roles
        init_roles()
        click.echo('Roles have been reset successfully.')
    
    @app.cli.command('create-admin')
    @click.argument('email')
    @click.argument('username')
    @click.argument('password')
    def create_admin(email, username, password):
        """Create an admin user if no admin exists."""
        from app.models.user import User
        from app import db
        
        # Check if admin already exists
        admin_exists = User.query.filter_by(is_admin=True).first() is not None
        
        if admin_exists:
            print("Admin user already exists! No changes made.")
            return
            
        # Create the admin user
        admin = User(
            email=email.lower(),
            username=username,
            is_admin=True,
            role_website='admin'
        )
        admin.password = password
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully!") 