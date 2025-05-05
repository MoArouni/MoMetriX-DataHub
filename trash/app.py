from flask import Flask, render_template, session, request, redirect
from sarasbeads.routes import sarasbeads_bp  # Non-scalable sarasbeads routes
from scalable_app import create_scalable_app  # Scalable app factory
from dotenv import load_dotenv
import os
from datetime import timedelta

# Load environment variables
load_dotenv('.env')

# Create the Flask app
app = Flask(__name__)

# Load configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = True
app.permanent_session_lifetime = timedelta(minutes=30)

# Register Blueprints
app.register_blueprint(sarasbeads_bp, url_prefix='/sarasbeads')
scalable_app = create_scalable_app()
app.register_blueprint(scalable_app, url_prefix='/app')


@app.route('/')
def index():
    """Render the HUB page as the default landing page."""
    user_role = session.get('user_role', 'Viewer')  # Default to Viewer

    return render_template('hub.html', global_role=user_role)


@app.context_processor
def inject_roles():
    """
    Makes `global_role` and `company_role` available in all templates.
    """
    global_role = session.get('user_role', None)

    company_role = None
    # Only try to extract company_id if it's in the current view args
    if request.blueprint and 'company' in request.blueprint.lower():
        company_id = request.view_args.get('company_id')  # Depends on how your routes are structured
        user_companies = session.get('user_companies', {})
        if company_id:
            company_role = user_companies.get(str(company_id), None)

    return dict(global_role=global_role, company_role=company_role)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Dummy login logic - replace with real DB logic
        username = request.form['username']
        if username == 'superadmin':
            session['user_id'] = 1
            session['global_role'] = 'admin'
            session['company_roles'] = {
                'sarasbeads': 'admin',
                'fluffypaws': 'viewer',
            }
        elif username == 'mod_sara':
            session['user_id'] = 2
            session['global_role'] = 'subscriber'
            session['company_roles'] = {
                'sarasbeads': 'moderator',
            }
        return redirect('/')
    return render_template('login.html')


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
