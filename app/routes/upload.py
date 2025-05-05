import os
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.tool import Tool
from app.forms.upload_forms import CSVUploadForm
from app.services.csv_validator import CSVValidator, CSVValidationError

# Create blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """Upload CSV data for a tool"""
    # Get user's tools for the dropdown
    user_tools = Tool.query.filter_by(creator_id=current_user.id).all()
    
    # Create form with dynamic choices
    form = CSVUploadForm()
    form.tool_id.choices = [(tool.id, tool.name) for tool in user_tools]
    
    if form.validate_on_submit():
        # Get the tool
        tool = Tool.query.get_or_404(form.tool_id.data)
        
        # Check if user has permission to upload to this tool
        if tool.creator_id != current_user.id:
            flash('You do not have permission to upload data to this tool.', 'error')
            return redirect(url_for('upload.upload_csv'))
            
        # Process the uploaded file
        csv_file = form.file.data
        filename = secure_filename(csv_file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the file
        csv_file.save(filepath)
        
        try:
            # Validate and process the CSV
            validator = CSVValidator(filepath, tool.schema_dict, form.has_headers.data)
            validator.validate()
            
            # Processing logic would go here
            # For now, just show success message
            flash('CSV file uploaded and validated successfully!', 'success')
            return redirect(url_for('tools.view', tool_id=tool.id))
            
        except CSVValidationError as e:
            flash(f'CSV validation error: {str(e)}', 'error')
        
    return render_template('upload/csv.html', form=form) 