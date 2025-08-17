#!/bin/bash

# Enable strict error handling
set -e

echo "=================================================="
echo "Starting MoMetriX DataHub Deployment Debug"
echo "=================================================="
echo "Timestamp: $(date)"
echo "Environment: Production"
echo "Render URL: ${RENDER_EXTERNAL_URL:-unknown}"
echo ""

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set!"
    exit 1
else
    echo "✅ DATABASE_URL is set (length: ${#DATABASE_URL} chars)"
    # Show sanitized URL (hide password)
    echo "   Database URL pattern: $(echo $DATABASE_URL | sed 's/:[^@]*@/:***@/g')"
fi

if [ -z "$FLASK_CONFIG" ]; then
    echo "⚠️  WARNING: FLASK_CONFIG not set, using default"
else
    echo "✅ FLASK_CONFIG: $FLASK_CONFIG"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY not set"
else
    echo "✅ SECRET_KEY is set (length: ${#SECRET_KEY} chars)"
fi

echo ""
echo "🔄 Testing database connection and initialization..."

python << END
import sys
import psycopg2
import os
import time
import sqlalchemy as sa
from sqlalchemy import text
import traceback

print("🔧 DEBUG: Starting Python database initialization script")
print(f"🔧 DEBUG: Python version: {sys.version}")

def debug_database_url():
    url = os.environ.get('DATABASE_URL', 'NOT_SET')
    if url == 'NOT_SET':
        print("❌ ERROR: DATABASE_URL not found in environment")
        return False
    
    # Parse URL components
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        print(f"✅ Database host: {parsed.hostname}")
        print(f"✅ Database port: {parsed.port}")
        print(f"✅ Database name: {parsed.path[1:] if parsed.path else 'unknown'}")
        print(f"✅ Database user: {parsed.username}")
        return True
    except Exception as e:
        print(f"❌ ERROR parsing DATABASE_URL: {e}")
        return False

def wait_for_db():
    print("🔄 Testing database connection...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"   Attempt {retry_count + 1}/{max_retries}")
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database connected successfully!")
            print(f"   PostgreSQL version: {version[0] if version else 'unknown'}")
            cursor.close()
            conn.close()
            return True
        except psycopg2.OperationalError as e:
            print(f"⚠️  Connection attempt {retry_count + 1} failed: {e}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)
        except KeyError:
            print("❌ ERROR: DATABASE_URL not set!")
            return False
        except Exception as e:
            print(f"❌ ERROR: Unexpected error connecting to database: {e}")
            traceback.print_exc()
            return False
    
    print("❌ ERROR: Failed to connect to database after all retries")
    return False

def check_and_create_tables():
    print("🔍 Checking if tables exist...")
    try:
        engine = sa.create_engine(os.environ['DATABASE_URL'])
        print(f"✅ SQLAlchemy engine created")
        
        with engine.connect() as conn:
            print("✅ SQLAlchemy connection established")
            
            # Check if users table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """))
            table_exists = result.scalar()
            print(f"🔍 Users table exists: {table_exists}")
            
            # Check all existing tables
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📋 Existing tables: {existing_tables}")
            
            if table_exists:
                print("✅ Tables already exist, no initialization needed.")
                return False
            else:
                print("⚠️  Tables don't exist. Will create them.")
                return True
                
    except Exception as e:
        print(f"❌ ERROR checking tables: {e}")
        traceback.print_exc()
        return True
    finally:
        try:
            engine.dispose()
            print("✅ SQLAlchemy engine disposed")
        except:
            pass

def create_tables():
    print("🏗️  Creating tables...")
    try:
        # Import the app and create tables
        sys.path.insert(0, '/opt/render/project/src')
        print("✅ Added project path to sys.path")
        
        from app import create_app, db
        print("✅ Imported Flask app and db")
        
        app = create_app('production')
        print("✅ Created Flask app with production config")
        
        with app.app_context():
            print("✅ Entered Flask app context")
            
            # Check app config
            print(f"🔧 App config database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT_SET')[:50]}...")
            
            db.create_all()
            print("✅ db.create_all() executed")
            
            # Verify tables were created
            engine = db.engine
            inspector = sa.inspect(engine)
            created_tables = inspector.get_table_names()
            print(f"📋 Created tables: {created_tables}")
            
            if 'users' in created_tables:
                print("✅ Users table successfully created")
            else:
                print("❌ ERROR: Users table not found after creation")
                return False
            
            # Initialize default data
            from app.utils.db_init import initialize_database
            print("✅ Imported initialize_database")
            
            initialize_database()
            print("✅ Database initialized with default data")
            
            return True
            
    except Exception as e:
        print(f"❌ ERROR creating tables: {e}")
        traceback.print_exc()
        return False

# Start debugging process
print("=" * 50)
if not debug_database_url():
    sys.exit(1)

print("=" * 50)
if not wait_for_db():
    sys.exit(1)

print("=" * 50)
needs_init = check_and_create_tables()

if needs_init:
    print("=" * 50)
    if not create_tables():
        print("❌ FATAL: Failed to create tables")
        sys.exit(1)
    print("✅ SUCCESS: Tables created and initialized!")
else:
    print("✅ SUCCESS: Tables already exist, no initialization needed")

print("🎉 Database initialization completed successfully!")
END

echo ""
echo "🚀 Running database migrations..."
flask db upgrade || echo "⚠️  Migration command failed, but continuing..."

echo ""
echo "🌟 Starting application server..."
echo "=================================================="
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app

# Run any pending migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app