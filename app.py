#to pass on values to the html files
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort

#importing the class from the analysis file
from analysis.sales_trend import SalesAnalysis

#some functions used in the application but don't have impact on the app itself
from main import load_data, get_latest_date, get_amount_rows, percentage  # Import functions from main.py

#pandas for analysis 
import pandas as pd 

#securing the filenames when uploading files
from werkzeug.utils import secure_filename

#passwords and confidential data
from dotenv import load_dotenv

# interacting with the operating system to do tasks like file management, environment variables, and system operations
import os

# functools: Provides higher-order functions like wraps, which is used to modify or enhance functions.
from functools import wraps

# jinja2: A templating engine for Python that allows you to generate HTML, XML, or other markup formats.
from jinja2 import Environment

# datetime: Supplies classes for manipulating dates and times.
from datetime import timedelta


#encrypts passwords 
import bcrypt

#secures the app 
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# CSRFProtect is used to add Cross-Site Request Forgery (CSRF) protection to the application.
# It ensures that any form submission or state-changing request includes a valid CSRF token,
# preventing malicious websites from performing actions on behalf of the authenticated user without their consent.
#csrf = CSRFProtect(app)

# Set session to be permanent and set a timeout
app.permanent_session_lifetime = timedelta(minutes=30)  # Session expires after 30 minutes
app.config['SESSION_COOKIE_SECURE'] = True  # Ensures that the cookie is only sent over HTTPS

# Add `sum` to the Jinja2 environment
app.jinja_env.globals.update(sum=sum)

# Load environment variables from secure.env
load_dotenv('.env')

# Read credentials from environment variables
app.secret_key = os.getenv('SECRET_KEY')
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')
csv_file_path = os.getenv('CSV_FILE_PATH')

users = {
    ADMIN_USER: bcrypt.hashpw(ADMIN_PASS.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
}

UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded files
ALLOWED_EXTENSIONS = {'csv'}  # Restrict file types to CSV

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/reveal/<section>', methods=['POST'])
def reveal_section(section):
    revealed = request.json.get('revealed', False)
    session[f'{section}_revealed'] = revealed
    return jsonify(success=True)
        
# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the file has an allowed extension and isn't empty."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and filename != ""


def admin_mode_required(f):
    """Decorator to ensure the user is in admin mode."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_mode', False):
            # Abort with a 403 Forbidden if the user is not in admin mode
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/upload_csv', methods=['POST'])
@admin_mode_required
def upload_csv():
    """Handle CSV file upload and process it."""
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    if file and allowed_file(file.filename):
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Load the CSV into a DataFrame and process it
        try:
            data = pd.read_csv(filepath)

            # Perform operations with the loaded data
            # For example: Save it to a database or render it on the page
            session['uploaded_file'] = filepath  # Save filepath in the session for further use
            return redirect(url_for('database'))
        except Exception as e:
            return f"Error processing file: {e}", 500
    else:
        return "Invalid file type. Only CSV files are allowed.", 400
    

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Handle login to enable admin tools."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password').encode('utf-8')  # Encode password to bytes for bcrypt

        # Check if the username is 'admin' and proceed with validation
        if username == 'admin':
            # Compare the entered password with the stored hashed password
            if bcrypt.checkpw(password, users.get(username).encode('utf-8')):
                # Grant admin mode access upon successful login
                session['admin_mode'] = True
                session['username'] = username
                session['logged_in'] = True  # Mark as logged in
                return redirect(url_for('home'))  # Redirect to the home page
            else:
                flash("Invalid username or password", "error")
                return redirect(url_for('admin'))  # Redirect back to login page
        else:
            flash("Only the 'admin' user can access the admin tools", "error")
            return redirect(url_for('admin'))  # Redirect back to login page

    return render_template('admin.html')

@app.route('/access_admin')
def access_admin():
    session.clear()  # Clear session or authentication
    session['admin_mode'] = True  # Enable admin mode
    session['uploaded_file'] = "data/sales.csv"
    flash("You are now in Admin Mode.", "success")
    return redirect(url_for('home'))  # Redirect to home

@app.route('/exit_admin')
def exit_admin():
    session.pop('admin_mode', None)  # Completely remove admin mode from session
    session.modified = True  # Ensure session updates
    flash("Admin mode disabled.", "info")
    return redirect(request.referrer or url_for('home'))  # Reload previous page or home


@app.route('/database')
def database():
    """Render the database page with the uploaded or default CSV file."""
    
    # Check if user is an admin (session variable `admin_mode` should be set to True)
    if session.get('admin_mode', False):
        filepath = "data/sales.csv"  # Real data file
    else:
        filepath = "data/dummy_sales.csv"  # Dummy data file for non-admin users
    
    # Check if the file exists
    if not os.path.exists(filepath):
        flash("Data file not found.", "error")
        return redirect(url_for('home'))
    
    # Get the latest date of sale
    latest_date = get_latest_date(filepath)
    rows = get_amount_rows(filepath)
    
    # Load data
    try:
        data = pd.read_csv(filepath)
        data = data.drop(columns=["Timestamp"])
        data_html = data.to_html(classes='data', index=False)
        return render_template('database.html', latest_date=latest_date, rows=rows, data_table=data_html)
    except Exception as e:
        return f"Error loading data: {e}", 500


@app.route('/home')
def home():
    admin_mode = session.get('admin_mode', False)  # Check if admin mode is enabled
    return render_template('home.html', admin_mode = admin_mode)  # Pass admin state to template

@app.route('/')
def index():
    """Render the HUB page as the default landing page."""
    return render_template('hub.html')


# Analysis page - Shows the results of the analysis
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    """Render the analysis page with the results of sales analysis."""
    # Load data
    filepath = session.get('uploaded_file', "data/sales.csv")
    if not os.path.exists(filepath):
        flash("Default data file not found.", "error")
        return redirect(url_for('home'))

    try:
        data = pd.read_csv(filepath)
        
        # Ensure 'Day of the sale' is in datetime format
        data['Day of the sale'] = pd.to_datetime(data['Day of the sale'], format='%m/%d/%Y', errors='coerce')
        
        # Handle any invalid dates (if any rows were not converted correctly)
        if data['Day of the sale'].isnull().any():
            flash("Warning: Some 'Day of the sale' entries couldn't be parsed as dates.", "warning")
        
    except Exception as e:
        flash(f"Error reading the data file: {str(e)}", "error")
        return redirect(url_for('home'))

    if data is not None:
        # Initialize the SalesAnalysis class
        analysis = SalesAnalysis(data)

        # Check for filter input
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        product_type_filter = request.form.get('product_type')
        collection_filter = request.form.get('collection')

        filtered_data = data

        # Apply date range filter if dates are provided
        if start_date and end_date:
            try:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                filtered_data = analysis.filter_day_range(start_date, end_date)
            except Exception as e:
                flash(f"Invalid date input: {str(e)}", "error")
                return redirect(url_for('analysis'))

        # Generate collection tables using table_collection method
        handmade_table = analysis.table_collection("Handmade / Beaded", filtered_data)
        sterling_silver_table = analysis.table_collection("Sterling Silver", filtered_data)
        gold_plated_table = analysis.table_collection("Gold Plated", filtered_data)

        # Generate the full database table using generate_db method
        full_database_table = analysis.generate_db(filtered_data)

        # Perform other analysis on filtered data
        average_sales = analysis.get_average_sales()
        table_month = analysis.table_month()
        table_week = analysis.table_week()
        table_payment = analysis.table_payment()

        # Render the analysis page with the filtered results and generated tables
        return render_template(
            'analysis.html',
            month=table_month.to_html(classes='data', header=True, index=True, escape=False),
            week=table_week.to_html(classes='data', header=True, index=True, escape=False),
            payment=table_payment.to_html(classes='data', header=True, index=True, escape=False),
            average_sales=average_sales,

            admin_mode=session.get('admin_mode', False),

            start_date = start_date.strftime('%Y-%m-%d') if start_date else '',
            end_date = end_date.strftime('%Y-%m-%d') if end_date else '',

            product_type_filter=product_type_filter,
            collection_filter=collection_filter,

            handmade_table=handmade_table.to_html(classes='data', header=True, index=True, escape=False),
            sterling_silver_table=sterling_silver_table.to_html(classes='data', header=True, index=True, escape=False),
            gold_plated_table=gold_plated_table.to_html(classes='data', header=True, index=True, escape=False),

            full_database_table=full_database_table.to_html(classes='data', header=True, index=True, escape=False)
        )
    else:
        flash("Error: Could not load the data", "error")
        return redirect(url_for('analysis'))




# Predictions page - Placeholder for predictions results
@app.route('/predictions')
def predictions():
    """Render the predictions page with sales predictions."""
    # Placeholder logic for predictions (you will need to add real prediction code)
    return render_template('predictions.html')

# Main check
if __name__ == '__main__':
    app.run(debug=True)
