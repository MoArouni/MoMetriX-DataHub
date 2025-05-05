from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional
import json

class ToolCreationForm(FlaskForm):
    """Form for creating a new data analysis tool"""
    name = StringField('Tool Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Make Public')
    submit = SubmitField('Create Tool')
    
class ToolConfigurationForm(FlaskForm):
    """Form for configuring tool settings"""
    chart_type = SelectField('Chart Type', choices=[
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('scatter', 'Scatter Plot'),
        ('table', 'Data Table')
    ])
    x_axis = StringField('X-Axis Field', validators=[DataRequired()])
    y_axis = StringField('Y-Axis Field', validators=[Optional()])
    grouping = StringField('Group By Field', validators=[Optional()])
    aggregation = SelectField('Aggregation Method', choices=[
        ('sum', 'Sum'),
        ('avg', 'Average'),
        ('count', 'Count'),
        ('min', 'Minimum'),
        ('max', 'Maximum')
    ])
    submit = SubmitField('Save Configuration')
    
    def to_json(self):
        """Convert form data to JSON for storing in database"""
        return json.dumps({
            'chart_type': self.chart_type.data,
            'x_axis': self.x_axis.data,
            'y_axis': self.y_axis.data,
            'grouping': self.grouping.data,
            'aggregation': self.aggregation.data
        })
        
    def from_json(self, json_data):
        """Load form data from JSON"""
        if not json_data:
            return
            
        data = json.loads(json_data)
        self.chart_type.data = data.get('chart_type')
        self.x_axis.data = data.get('x_axis')
        self.y_axis.data = data.get('y_axis')
        self.grouping.data = data.get('grouping')
        self.aggregation.data = data.get('aggregation') 