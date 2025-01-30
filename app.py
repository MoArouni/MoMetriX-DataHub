from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from analysis.sales_trend import SalesAnalysis
from main import load_data, get_latest_date, get_amount_rows, percentage  # Import functions from main.py
import pandas as pd 
from werkzeug.utils import secure_filename
import os
from functools import wraps
from jinja2 import Environment

app = Flask(__name__)
# Add `sum` to the Jinja2 environment
app.jinja_env.globals.update(sum=sum)



app.secret_key = 'your_secret_key'  # Required for session management

# Dummy credentials for testing
users = {'demonstrator': 'demon', 'admin': 'kingM0_18', 'khalil': 'kingM0_18', 'sarah' : 'kingM0_18', 'yusuf' : 'kingM0_18'}

UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded files
ALLOWED_EXTENSIONS = {'csv'}  # Restrict file types to CSV

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/reveal/<section>', methods=['POST'])
def reveal_section(section):
    revealed = request.json.get('revealed', False)
    session[f'{section}_revealed'] = revealed
    return jsonify(success=True)


@app.route('/toggle_demo_mode')
def toggle_demo_mode():
    """Toggle the demo mode on or off based on the session state."""
    if 'username' in session:
        if session.get('demo_mode', False):
            # If demo mode is currently on, turn it off and set admin mode on
            session['demo_mode'] = False
            session['admin_mode'] = True
        else:
            # If demo mode is currently off, turn it on and set admin mode off
            session['demo_mode'] = True
            session['admin_mode'] = False
        return redirect(url_for('home'))  # Redirect to home page after toggle
    return redirect(url_for('login'))



@app.route('/toggle_admin_mode')
def toggle_admin_mode():
    """Ensure admin mode is opposite of demo mode."""
    if 'username' in session:
        # Set admin_mode based on the opposite of demo_mode
        session['admin_mode'] = not session.get('demo_mode', False)
        return redirect(url_for('home'))  # Redirect to home page
    return redirect(url_for('login'))

# Protect routes with login requirement
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap



# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_csv', methods=['POST'])
@login_required
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
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')  
        password = request.form.get('password')

        if username == 'demonstrator' and password == users.get(username):
            # When demonstrator logs in, set demo mode in session
            session['demo_mode'] = True
            session['admin_mode'] = False
            session['username'] = username
            session['logged_in'] = True  # Mark as logged in
            return redirect(url_for('home'))  # Redirect to home after login as demonstrator
        elif username in users and password == users.get(username):
            # Handle regular user login
            session['logged_in'] = True
            session['username'] = username
            session['demo_mode'] = False  # Ensure demo mode is off for regular users
            session['admin_mode'] = True
            return redirect(url_for('home'))  # Redirect to home page for regular user
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))  # Redirect back to login page with error

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()  # Clear session or authentication
    return redirect(url_for('login'))  # Redirect to login page







@app.route('/database')
@login_required
def database():
    """Render the database page with the uploaded or default CSV file."""
    # Use uploaded file if available
    filepath = session.get('uploaded_file', "data/sales.csv")
    if not os.path.exists(filepath):
        flash("Default data file not found.", "error")
        return redirect(url_for('home'))

    
    # Get the latest date of sale
    latest_date = get_latest_date(filepath)
    rows = get_amount_rows(filepath)
    # Load data
    try:
        data = pd.read_csv(filepath)
        data = data.drop(columns=["Timestamp"])
        data_html = data.to_html(classes='data', index=False)
        return render_template('database.html', latest_date=latest_date, rows = rows, data_table=data_html)
    except Exception as e:
        return f"Error loading data: {e}", 500

@app.route('/home')
@login_required
def home():
    # Redirect based on whether demo_mode is set
    if 'demo_mode' in session and session['demo_mode']:
        demo_mode = "ON"
        admin_mode = "OFF"
    else:
        demo_mode = "OFF"
        admin_mode = "ON"
    
    return render_template('home.html', demo_mode=demo_mode, admin_mode=admin_mode)

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))


# Analysis page - Shows the results of the analysis
@app.route('/analysis', methods=['GET', 'POST'])
@login_required
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

            demo_mode=session.get('demo_mode', False),
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



@app.route('/verify_pin', methods=['POST'])
@login_required
def verify_pin():
    """Handle PIN verification."""
    pin = request.form.get('pin')  # Get PIN from the form
    correct_pin = '1234'  # Set your correct PIN here

    if pin == correct_pin:
        # If the PIN is correct, mark the session as PIN verified
        session['pin_verified'] = True
        flash("PIN verified! Sensitive data is now visible.", "success")
    else:
        # If the PIN is incorrect, display an error message
        flash("Incorrect PIN. Please try again.", "error")

    return redirect(url_for('analysis'))


# Predictions page - Placeholder for predictions results
@app.route('/predictions')
@login_required
def predictions():
    """Render the predictions page with sales predictions."""
    # Placeholder logic for predictions (you will need to add real prediction code)
    return render_template('predictions.html')

# Main check
if __name__ == '__main__':
    app.run(debug=True)
