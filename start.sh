#!/bin/bash

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
python << END
import sys
import psycopg2
import os
import time

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

wait_for_db()
END

# Initialize database (create all tables and seed data)
echo "Initializing database..."
flask init-db --force

# Run any pending migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app