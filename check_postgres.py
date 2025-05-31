#!/usr/bin/env python
"""
Script to check PostgreSQL connection and settings
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgres_connection():
    """Check if we can connect to PostgreSQL and verify settings"""
    print("=== PostgreSQL Connection Check ===")
    
    # Database connection parameters
    db_params = {}
    db_params['user'] = os.environ.get('DB_USER', 'postgres')
    db_params['password'] = os.environ.get('DB_PASSWORD', 'postgres')
    db_params['host'] = os.environ.get('DB_HOST', 'localhost')
    db_params['port'] = os.environ.get('DB_PORT', '5432')
    db_params['database'] = 'MoMetriXHub'
    
    print("\nEnvironment variables:")
    for key, value in db_params.items():
        if key == 'password':
            # Don't show the actual password
            print(f"  {key}: {'*' * len(value) if value else 'Not set'}")
        else:
            print(f"  {key}: {value}")
    
    # Check DATABASE_URL if set
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"  DATABASE_URL: {database_url.replace(db_params['password'], '*'*len(db_params['password']) if db_params['password'] else '')}")
    else:
        print("  DATABASE_URL: Not set")
    
    print("\nAttempting to connect to PostgreSQL...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Connected successfully to PostgreSQL:\n{version}")
        
        # Check if necessary tables exist
        print("\nChecking for essential tables:")
        essential_tables = [
            'users', 'roles_website', 'roles_company', 'companies'
        ]
        
        for table in essential_tables:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)", 
                (table,)
            )
            exists = cursor.fetchone()[0]
            print(f"  {table}: {'✓ Exists' if exists else '✗ Not found'}")
        
        # Close connection
        cursor.close()
        conn.close()
        print("\nConnection test completed successfully!")
        return True
    
    except Exception as e:
        print(f"\nError connecting to PostgreSQL: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL server is running")
        print("2. Verify your database credentials in .env file")
        print("3. Ensure the 'MoMetriXHub' database has been created")
        print("4. Check that your PostgreSQL server accepts connections from localhost")
        return False

if __name__ == "__main__":
    check_postgres_connection() 