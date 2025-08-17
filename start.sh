#!/bin/bash

# Wait for database to be ready and check/create tables
echo "Waiting for PostgreSQL to be ready..."
python << END
import sys
import psycopg2
import os
import time
import sqlalchemy as sa
from sqlalchemy import text

def wait_for_db():
    while True:
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            conn.close()
            return True
        except psycopg2.OperationalError:
            time.sleep(1)
        except KeyError:
            print("DATABASE_URL not set!")
            sys.exit(1)

def check_and_create_tables():
    print("Checking if tables exist...")
    engine = sa.create_engine(os.environ['DATABASE_URL'])
    
    try:
        with engine.connect() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("Tables already exist.")
                return False
            else:
                print("Tables don't exist. Will create them.")
                return True
    except Exception as e:
        print(f"Error checking tables: {e}")
        return True
    finally:
        engine.dispose()

wait_for_db()
needs_init = check_and_create_tables()

if needs_init:
    print("Creating tables...")
    # Import the app and create tables
    sys.path.insert(0, '/opt/render/project/src')
    from app import create_app, db
    from app.utils.db_init import initialize_database
    
    app = create_app('production')
    with app.app_context():
        db.create_all()
        initialize_database()
        print("Tables created and initialized successfully!")
else:
    print("Tables exist, skipping initialization.")
END

# Run any pending migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app