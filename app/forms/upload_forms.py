from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired

class CSVUploadForm(FlaskForm):
    """Form for uploading CSV data files"""
    file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    tool_id = SelectField('Tool', coerce=int, validators=[DataRequired()])
    has_headers = BooleanField('File has headers', default=True)
    submit = SubmitField('Upload') 