import click
from flask.cli import with_appcontext
from app import db
from app.utils.db_init import initialize_database
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError, ProgrammingError


def register_commands(app):
    """Register Flask CLI commands"""
    
    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Initialize the database with schema and default data."""
        click.echo('Initializing the database...')
        
        # Create a connection to check if tables exist
        engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        inspector = sa.inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            if click.confirm('Database tables already exist. Do you want to drop all tables and recreate?'):
                # Drop all tables if they exist
                db.drop_all()
                click.echo('Dropped existing tables.')
            else:
                click.echo('Aborted. Database remains unchanged.')
                return
        
        # Create tables
        db.create_all()
        click.echo('Created new tables.')
        
        # Initialize with default data
        initialize_database()
        click.echo('Database initialization complete.')
    
    @app.cli.command('create-db')
    @with_appcontext
    def create_db():
        """Create the PostgreSQL database if it doesn't exist"""
        # Use the URI and database name from the current config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_name = app.config['DB_NAME']
        
        click.echo(f'Attempting to create database {db_name} if it does not exist...')
        
        # Connect to the default postgres database (postgres)
        db_uri_parts = db_uri.split('/')
        db_uri_without_db = '/'.join(db_uri_parts[:-1]) + '/postgres'
        engine = sa.create_engine(db_uri_without_db)
        conn = engine.connect()
        conn.execute(sa.text("COMMIT"))  # Close any open transactions
        
        # Check if database exists
        result = conn.execute(sa.text(f"SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": db_name})
        exists = result.scalar() == 1
        
        if not exists:
            try:
                # Create database if it doesn't exist
                conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
                click.echo(f'Database {db_name} created successfully.')
            except Exception as e:
                click.echo(f'Error creating database: {str(e)}')
        else:
            click.echo(f'Database {db_name} already exists.')
        
        conn.close()
        engine.dispose()
    
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
    
    @app.cli.command('create-subscription-plans')
    @with_appcontext
    def create_subscription_plans_command():
        """Initialize subscription plans in the database."""
        from app.scripts.create_subscription_plans import create_subscription_plans
        create_subscription_plans()
        click.echo('Subscription plans have been created.')

    @click.command('migrate-products-to-embellishments')
    @with_appcontext
    def migrate_products_to_embellishments():
        """Migrate products to use embellishments instead of active status"""
        from app.models.product import Product, Embellishment
        from app import db
        from sqlalchemy.sql import text
        from datetime import datetime
        
        click.echo('Starting migration of products to use embellishments...')
        
        # First, close all SQLAlchemy connections to avoid locks
        db.session.close()
        db.engine.dispose()
        
        # Create the embellishment tables first if they don't exist
        try:
            db.create_all()
            click.echo('Created all necessary tables.')
        except Exception as e:
            click.echo(f'Error creating tables: {str(e)}')
            return
        
        # Check if embellishments table was created successfully
        inspector = db.inspect(db.engine)
        if not inspector.has_table('embellishments'):
            click.echo('Failed to create embellishments table. Please check database permissions.')
            return
        
        try:
            # Connect using SQLAlchemy's engine
            with db.engine.connect() as conn:
                # Check if 'active' column exists in products table
                result = conn.execute(sa.text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'products' AND column_name = 'active'"
                ))
                
                if not result.fetchone():
                    click.echo('No active column found in products table. Migration may have already been applied.')
                    return
                
                # For each company, create a default embellishment
                click.echo('Creating default embellishments for each company...')
                
                # Get all companies
                result = conn.execute(sa.text("SELECT id FROM companies"))
                company_ids = [row[0] for row in result.fetchall()]
                
                for company_id in company_ids:
                    # Get categories for this company
                    result = conn.execute(sa.text(
                        "SELECT id FROM product_categories WHERE company_id = :company_id"
                    ), {"company_id": company_id})
                    category_ids = [row[0] for row in result.fetchall()]
                    
                    # Create default embellishment for this company
                    result = conn.execute(sa.text("""
                        INSERT INTO embellishments (name, description, company_id, created_at, updated_at)
                        VALUES (:name, :description, :company_id, :created_at, :updated_at)
                        RETURNING id
                    """), {
                        "name": "Standard",
                        "description": "Default embellishment for standard products",
                        "company_id": company_id,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                    
                    embellishment_id = result.fetchone()[0]
                    
                    # Associate embellishments with product types
                    for category_id in category_ids:
                        conn.execute(sa.text("""
                            INSERT INTO embellishment_product_types (embellishment_id, product_type_id)
                            VALUES (:embellishment_id, :product_type_id)
                        """), {
                            "embellishment_id": embellishment_id,
                            "product_type_id": category_id
                        })
                    
                    # Get active products for this company
                    result = conn.execute(sa.text(
                        "SELECT id FROM products WHERE company_id = :company_id AND active = true"
                    ), {"company_id": company_id})
                    active_product_ids = [row[0] for row in result.fetchall()]
                    
                    # Associate active products with the Standard embellishment
                    for product_id in active_product_ids:
                        conn.execute(sa.text("""
                            INSERT INTO product_embellishments (product_id, embellishment_id)
                            VALUES (:product_id, :embellishment_id)
                        """), {
                            "product_id": product_id,
                            "embellishment_id": embellishment_id
                        })
                
                # In PostgreSQL, we can directly drop columns using ALTER TABLE
                conn.execute(sa.text("ALTER TABLE products DROP COLUMN active"))
                
                click.echo('Migration completed successfully.')
                
        except Exception as e:
            click.echo(f'Error during migration: {str(e)}')
            return

    # Add all commands to the app
    app.cli.add_command(create_admin)
    app.cli.add_command(create_subscription_plans_command)
    app.cli.add_command(migrate_products_to_embellishments)
    