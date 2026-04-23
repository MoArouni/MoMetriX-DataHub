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

Install dev dependencies and run the suite:

```
pip install -r requirements-dev.txt
pytest
```

The analytics tests run on pure DataFrames (no DB / app context) and cover
the canonical contract (`_prepare`), dashboard summary, day/monthly/store/
category aggregations, and report buckets.

## Analytics Data Contract

All analytics functions in `app/services/analytics_service.py` operate on
a canonical pandas DataFrame produced by
`AnalyticsService.get_company_sales_data` (which internally runs
`AnalyticsService._prepare`). This keeps metrics consistent regardless of
source (manual entry, CSV import, or — later — external integrations).

Canonical columns (see `AnalyticsService.CANONICAL_COLUMNS`):

| column             | type                | notes                               |
|--------------------|---------------------|-------------------------------------|
| `sale_id`          | int                 | unique per row                      |
| `sale_date`        | `datetime64[ns]`    | midnight when source is date-only   |
| `store_name`       | str                 | `"Unknown Store"` if missing        |
| `product_category` | str                 | `"Uncategorized"` if missing        |
| `product_name`     | str                 | `"Unknown Product"` if missing      |
| `quantity`         | int                 | defaults to 1                       |
| `total`            | float               | canonical revenue per row           |
| `card_amount`      | float               |                                     |
| `cash_amount`      | float               |                                     |
| `payment_method`   | str                 |                                     |
| `embellishments`   | str                 | `"None"` if empty                   |
| `notes`            | str \| None         |                                     |
| `day_of_week`      | str                 | derived from `sale_date`            |
| `month`            | str                 | derived from `sale_date`            |
| `year`             | int                 | derived from `sale_date`            |

Rules applied in `_prepare`:

- Rows without a parseable `sale_date` are dropped.
- Missing money fields default to `0.0`.
- Revenue fallback: when `total <= 0`, `total` is replaced with
  `card_amount + cash_amount`.
- Extra source-specific columns (e.g. `source`, `external_id` from future
  integrations) are preserved after the canonical columns.

## Deployment

For production deployment, set the following environment variables:

- `FLASK_CONFIG=production`
- `SECRET_KEY=your_secure_key`
- `DATABASE_URL=your_database_url`

## License

MIT
