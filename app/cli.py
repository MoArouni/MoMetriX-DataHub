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

    @app.cli.command('seed-faqs')
    @with_appcontext
    def seed_faqs():
        """Seed default FAQs for the application."""
        from app.models.qa import Question, Answer
        from app.models.user import User
        
        # Get or create admin user for FAQ authoring
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            click.echo('No admin user found. Please create an admin user first.')
            return
        
        # Default FAQs
        faqs = [
            {
                'title': 'How do I join an existing company as a moderator?',
                'content': '''To join an existing company as a moderator, follow these steps:

1. **Start the Join Process**: Click on "Join Company" in the navigation menu or visit /join/
2. **Email Verification**: Enter your email address and verify it with the 6-digit code sent to your email
3. **Select Company**: Choose the company you want to join from the dropdown list and optionally add a message
4. **Wait for Approval**: The company admin will receive an email notification and review your request
5. **Accept Invitation**: Once approved, you'll receive an email with an invitation link and passcode
6. **Complete Registration**: Follow the link, enter the passcode, and complete your profile

The company admin (not the global website admin) will review and approve your request. You'll be notified via email about the decision.''',
                'answer': '''The join process is designed to be secure and requires approval from the company administrator. Make sure to use a valid email address as all communications will be sent there.'''
            },
            {
                'title': 'What are the different permission levels for moderators?',
                'content': '''When a company admin approves your join request, they can assign one of three permission levels:

**Data Entry Only**
- Add and edit product data
- Basic data entry capabilities
- Cannot view sales reports

**Data Entry + Daily Sales View**
- All data entry permissions
- View daily sales reports
- Access to basic analytics

**Full Access**
- Complete access to all company data
- View all sales reports and analytics
- Manage products, stores, and locations
- Access to advanced features

The company admin can change your permission level at any time based on your role and responsibilities.''',
                'answer': '''Permission levels are set by the company admin and determine what features and data you can access within the company's account.'''
            },
            {
                'title': 'How do I reset my password?',
                'content': '''If you've forgotten your password, you can reset it easily:

1. **Go to Login Page**: Visit the login page
2. **Click "Forgot Password"**: Look for the "Forgot your password?" link
3. **Enter Your Email**: Provide the email address associated with your account
4. **Check Your Email**: You'll receive a password reset link
5. **Follow the Link**: Click the link in the email (valid for 1 hour)
6. **Set New Password**: Enter and confirm your new password
7. **Login**: Use your new password to access your account

If you don't receive the email, check your spam folder or contact support.''',
                'answer': '''Password reset links expire after 1 hour for security reasons. If the link expires, you'll need to request a new one.'''
            },
            {
                'title': 'What subscription plans are available?',
                'content': '''MoMetriX DataHub offers several subscription plans to meet different business needs:

**Free Plan**
- Basic features for small businesses
- Limited data storage
- Basic analytics

**Professional Plan**
- Advanced analytics and reporting
- Increased data storage
- Priority support
- Multiple user accounts

**Enterprise Plan**
- Unlimited data storage
- Advanced integrations
- Custom features
- Dedicated support

Contact our sales team for custom enterprise solutions and pricing information.''',
                'answer': '''You can upgrade or downgrade your subscription plan at any time through your account settings. Changes take effect at the next billing cycle.'''
            },
            {
                'title': 'How do I create a company account?',
                'content': '''To create a company account:

1. **Register**: Create a user account with subscriber role
2. **Verify Email**: Complete email verification if required
3. **Create Company**: You'll be redirected to company creation page
4. **Fill Details**: Enter company name, email, and contact information
5. **Choose Plan**: Select a subscription plan that fits your needs
6. **Complete Setup**: Finish the setup process

As the company creator, you automatically become the company administrator with full access to manage join requests, user permissions, and company settings.''',
                'answer': '''Only users with subscriber role can create companies. The company creator becomes the admin and can invite other users to join as moderators.'''
            },
            {
                'title': 'How do I manage join requests for my company?',
                'content': '''As a company administrator, you can manage join requests through the admin panel:

1. **Access Admin Panel**: Look for "Join Requests" in your navigation menu
2. **Review Requests**: See all pending, approved, and declined requests
3. **Review Details**: Click on a request to see the applicant's message and details
4. **Set Permissions**: Choose the appropriate permission level for the moderator
5. **Approve or Decline**: Make your decision and the applicant will be notified
6. **Track Invites**: Monitor sent invitations and their status

You'll receive email notifications when new join requests are submitted.''',
                'answer': '''Only company administrators (the company owner) can review and approve join requests. Regular moderators cannot manage other users.'''
            },
            {
                'title': 'What data can I track with MoMetriX DataHub?',
                'content': '''MoMetriX DataHub allows you to track comprehensive business data:

**Sales Data**
- Daily, weekly, monthly sales reports
- Revenue tracking and trends
- Product performance analytics

**Product Management**
- Product catalogs and categories
- Inventory tracking
- Product performance metrics

**Store Management**
- Multiple store locations
- Store-specific analytics
- Location-based reporting

**Customer Analytics**
- Customer behavior patterns
- Purchase history
- Customer segmentation

All data is securely stored and can be exported for further analysis.''',
                'answer': '''The platform is designed to handle various types of business data with robust analytics and reporting capabilities.'''
            },
            {
                'title': 'Is my data secure?',
                'content': '''Yes, we take data security very seriously:

**Encryption**
- All data is encrypted in transit and at rest
- Secure HTTPS connections for all communications

**Access Control**
- Role-based permissions
- Company-specific data isolation
- Secure authentication systems

**Backup & Recovery**
- Regular automated backups
- Disaster recovery procedures
- Data redundancy

**Compliance**
- GDPR compliant data handling
- Regular security audits
- Industry-standard security practices

Your company's data is completely isolated from other companies and only accessible to authorized users.''',
                'answer': '''We follow industry best practices for data security and privacy. Your data is never shared with third parties without your explicit consent.'''
            }
        ]
        
        created_count = 0
        for faq_data in faqs:
            # Check if question already exists
            existing = Question.query.filter_by(title=faq_data['title']).first()
            if existing:
                click.echo(f'FAQ already exists: {faq_data["title"]}')
                continue
            
            # Create question
            question = Question(
                title=faq_data['title'],
                content=faq_data['content'],
                user_id=admin_user.id
            )
            db.session.add(question)
            db.session.flush()  # Get the question ID
            
            # Create answer
            answer = Answer(
                content=faq_data['answer'],
                question_id=question.id,
                user_id=admin_user.id
            )
            db.session.add(answer)
            created_count += 1
        
        db.session.commit()
        click.echo(f'Successfully created {created_count} FAQs.')

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
    