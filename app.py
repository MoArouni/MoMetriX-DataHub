#!/usr/bin/env python3
"""
Main application entry point for MoMetriX DataHub
"""

import os
from app import create_app

# Create the Flask application
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    ) 