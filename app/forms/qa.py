from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=10, max=200)])
    content = TextAreaField('Question Details', validators=[DataRequired(), Length(min=30)])
    submit = SubmitField('Post Question')

class AnswerForm(FlaskForm):
    content = TextAreaField('Your Answer', validators=[DataRequired(), Length(min=30)])
    submit = SubmitField('Post Answer') 