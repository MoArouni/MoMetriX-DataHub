from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length
import json

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    content_blocks = HiddenField('Content Blocks')  # Will store JSON
    submit = SubmitField('Publish Post')
    
    def get_content_blocks(self):
        """Parse content blocks from form data"""
        try:
            if self.content_blocks.data:
                blocks = json.loads(self.content_blocks.data)
                if isinstance(blocks, list) and len(blocks) > 0:
                    return blocks
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Default empty text block
        return [{"type": "text", "content": ""}]
    
    def set_content_blocks(self, blocks):
        """Set content blocks to form"""
        self.content_blocks.data = json.dumps(blocks) 

