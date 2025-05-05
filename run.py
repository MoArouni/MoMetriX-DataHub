import os
from app import create_app, db
from app.models import User, Company, Tool, Sale
from flask_migrate import Migrate

# Create app instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """
    Creates a shell context that adds the database instance and
    models to the shell session
    """
    return dict(db=db, User=User, Company=Company, Tool=Tool, Sale=Sale)

if __name__ == '__main__':
    # Run the app
    app.run(debug=True) 