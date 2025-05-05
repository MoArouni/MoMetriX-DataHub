# Data Analytics Hub

A Flask-based web application for data analytics, tool creation, and visualization.

## Features

- User authentication and management
- Company-based collaboration
- Custom analytics tool creation
- CSV data uploading and validation
- Interactive data visualization
- Dashboard sharing and permissions

## Project Structure

```
BIG_FLASK_APP/
│
├── app/                            # Main Flask app package
│   ├── __init__.py                 # App factory, extensions, blueprints
│   ├── config.py                   # Config for dev, prod, etc.
│   │
│   ├── models/                     # SQLAlchemy models
│   ├── forms/                      # WTForms forms 
│   ├── routes/                     # View routes/blueprints
│   ├── services/                   # Business logic
│   ├── templates/                  # Jinja2 templates
│   ├── static/                     # Static assets
│   └── utils/                      # Helper functions
│
├── migrations/                     # Flask-Migrate folder
├── tests/                          # Unit & integration tests
├── run.py                          # Entry point
├── requirements.txt
└── README.md
```

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: 
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install requirements:
   ```
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the development server:
   ```
   python run.py
   ```
   or
   ```
   flask run
   ```

## Development

### Database Migrations

After changing models:

```
flask db migrate -m "Description of changes"
flask db upgrade
```

### Running Tests

```
pytest
```

## Deployment

For production deployment, set the following environment variables:

- `FLASK_CONFIG=production`
- `SECRET_KEY=your_secure_key`
- `DATABASE_URL=your_database_url`

## License

MIT
