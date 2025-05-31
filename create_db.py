#!/usr/bin/env python
"""
Script to create the MoMetriXHub database in PostgreSQL
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the MoMetriXHub database if it doesn't exist"""
    print("Attempting to create MoMetriXHub database...")
    
    # Get connection parameters from environment variables or use defaults
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    
    # Connect to the default PostgreSQL database
    try:
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='MoMetriXHub'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating database 'MoMetriXHub'...")
            cursor.execute("CREATE DATABASE \"MoMetriXHub\"")
            print("Database created successfully!")
        else:
            print("Database 'MoMetriXHub' already exists.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        return False

if __name__ == "__main__":
    if create_database():
        print("Database creation succeeded. You can now run your application.")
        sys.exit(0)
    else:
        print("Database creation failed. Please check your PostgreSQL configuration.")
        sys.exit(1) 