#!/usr/bin/env python
"""
PostgreSQL database setup script for MoMetriX DataHub
This script will:
1. Create the PostgreSQL database if it doesn't exist
2. Run migrations
3. Initialize the database with default data including admin user
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def run_command(command):
    """Run a command and print its output"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.output}")
        print(f"Error output: {e.stderr}")
        return False

def run_flask_command(command):
    """Run a Flask command using python -m flask"""
    return run_command(f"python -m flask {command}")

def check_environment_variables():
    """Check for required environment variables and print them"""
    print("\nChecking environment variables...")
    
    # Required variables
    required_vars = ['DATABASE_URL']
    optional_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 
                    'ADMIN_EMAIL', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']
    
    all_present = True
    
    # Check DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("WARNING: DATABASE_URL is not set! Will use individual DB settings instead.")
        
        # Check if individual DB settings are provided
        for var in ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']:
            value = os.environ.get(var)
            print(f"  {var}: {'✓ Set' if value else '✗ NOT SET'}")
            if not value and var in ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']:
                all_present = False
    else:
        print("✓ DATABASE_URL is set!")
    
    # Check admin user settings
    print("\nAdmin user settings:")
    for var in ['ADMIN_EMAIL', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']:
        value = os.environ.get(var)
        print(f"  {var}: {'✓ Set' if value else '✗ Using default'}")
    
    if not all_present:
        print("\nWARNING: Some required environment variables are missing.")
        print("See .env.example for required variables.")
        
        # Ask if the user wants to continue
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True

def main():
    """Main function to setup PostgreSQL database"""
    print("Setting up PostgreSQL database for MoMetriX DataHub...")
    
    # First check environment variables
    if not check_environment_variables():
        print("Setup aborted.")
        return 1
    
    # Check if Flask is installed
    try:
        import flask
        print(f"Flask version: {flask.__version__}")
    except ImportError:
        print("Flask is not installed. Please run: pip install -r requirements.txt")
        return 1
    
    # Set the FLASK_APP environment variable
    os.environ['FLASK_APP'] = 'run.py'
    print(f"FLASK_APP set to: {os.environ.get('FLASK_APP')}")
    
    # Create the database if it doesn't exist
    create_result = run_flask_command("create-db")
    if not create_result:
        print("Warning: create-db command failed, but continuing setup...")
        print("This might be okay if you created the database separately using create_db.py")
    
    # Run migrations
    if not run_flask_command("db upgrade"):
        print("Failed to run migrations. Exiting.")
        return 1
    
    # Initialize the database with default data
    if not run_flask_command("init-db"):
        print("Failed to initialize database. This may be fine if it already exists.")
    
    print("\nPostgreSQL database setup complete!")
    print("You can now run the application with: python -m flask run")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 