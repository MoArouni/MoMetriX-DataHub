from app import db
from datetime import datetime
import json

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Will store JSON blocks
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    @property
    def content_blocks(self):
        """Parse content as JSON blocks, fallback to simple text for old posts"""
        try:
            blocks = json.loads(self.content)
            if isinstance(blocks, list):
                return blocks
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback for old posts - convert plain text to single text block
        return [{"type": "text", "content": self.content}]
    
    @content_blocks.setter
    def content_blocks(self, blocks):
        """Store blocks as JSON"""
        self.content = json.dumps(blocks)
    
    @property
    def preview_text(self):
        """Generate a plain text preview from content blocks"""
        preview_parts = []
        
        for block in self.content_blocks:
            if block.get('type') in ['text', 'heading']:
                content = block.get('content', '')
                # Strip HTML tags for preview
                import re
                clean_content = re.sub(r'<[^>]+>', '', content)
                if clean_content.strip():
                    preview_parts.append(clean_content.strip())
        
        preview = ' '.join(preview_parts)
        return preview[:200] + '...' if len(preview) > 200 else preview
    
    def __repr__(self):
        return f'<BlogPost {self.title}>' 