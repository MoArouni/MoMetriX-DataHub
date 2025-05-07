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
        import sqlite3
        import time
        import os
        from app.config import basedir
        
        click.echo('Starting migration of products to use embellishments...')
        
        # Get the database path from the app configuration
        db_path = os.path.join(basedir, '..', 'dev.sqlite')
        click.echo(f'Database path: {db_path}')
        
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
            # Open a direct connection to SQLite
            click.echo('Opening direct connection to SQLite...')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if 'active' column exists in products table
            cursor.execute("PRAGMA table_info(products)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'active' not in columns:
                click.echo('No active column found in products table. Migration may have already been applied.')
                conn.close()
                return
            
            # For each company, create a default embellishment
            click.echo('Creating default embellishments for each company...')
            companies = {}
            company_categories = {}
            
            # Get all companies
            cursor.execute("SELECT id FROM companies")
            for row in cursor.fetchall():
                company_id = row[0]
                companies[company_id] = True
                
                # Get categories for this company
                cursor.execute("SELECT id FROM product_categories WHERE company_id = ?", (company_id,))
                company_categories[company_id] = [row[0] for row in cursor.fetchall()]
                
                # Create default embellishment for this company
                cursor.execute("""
                    INSERT INTO embellishments (name, description, company_id, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?)
                """, ("Standard", "Default embellishment for standard products", company_id, 
                     datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
                
                # Get the embellishment ID
                embellishment_id = cursor.lastrowid
                
                # Associate embellishments with product types
                if company_categories[company_id]:
                    for category_id in company_categories[company_id]:
                        cursor.execute("""
                            INSERT INTO embellishment_product_types (embellishment_id, product_type_id) 
                            VALUES (?, ?)
                        """, (embellishment_id, category_id))
                
                # Get active products for this company
                cursor.execute("SELECT id FROM products WHERE company_id = ? AND active = 1", (company_id,))
                active_product_ids = [row[0] for row in cursor.fetchall()]
                
                # Associate active products with the Standard embellishment
                for product_id in active_product_ids:
                    cursor.execute("""
                        INSERT INTO product_embellishments (product_id, embellishment_id) 
                        VALUES (?, ?)
                    """, (product_id, embellishment_id))
            
            # Commit the changes
            conn.commit()
            
            # Try to drop the active column - SQLite requires creating a new table for this
            click.echo('Dropping active column from products table...')
            # Get product table schema without the active column
            cursor.execute("PRAGMA table_info(products)")
            columns_info = [column for column in cursor.fetchall() if column[1] != 'active']
            
            # Create column definitions for the new table
            column_defs = []
            for col in columns_info:
                name = col[1]
                type_info = col[2]
                nullable = "NOT NULL" if col[3] == 1 else ""
                default = f"DEFAULT {col[4]}" if col[4] is not None else ""
                pk = "PRIMARY KEY" if col[5] == 1 else ""
                column_defs.append(f"{name} {type_info} {nullable} {default} {pk}".strip())
            
            # Create a temporary table with all columns except active
            cursor.execute(f"""
                CREATE TABLE products_new (
                    {', '.join(column_defs)}
                )
            """)
            
            # Copy data from products to products_new
            columns_to_copy = [col[1] for col in columns_info]
            cursor.execute(f"""
                INSERT INTO products_new SELECT {', '.join(columns_to_copy)} FROM products
            """)
            
            # Drop the old table and rename the new one
            cursor.execute("DROP TABLE products")
            cursor.execute("ALTER TABLE products_new RENAME TO products")
            
            # Recreate indexes and foreign keys (if any)
            # This would need to be customized based on your schema
            
            # Commit and close
            conn.commit()
            conn.close()
            
            click.echo('Migration completed successfully.')
            
        except Exception as e:
            click.echo(f'Error during migration: {str(e)}')
            if 'conn' in locals():
                conn.close()
            return

    # Add all commands to the app
    app.cli.add_command(create_admin)
    app.cli.add_command(create_subscription_plans_command)
    app.cli.add_command(migrate_products_to_embellishments)
    