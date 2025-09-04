from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.blog import BlogPost
from app.forms.blog import BlogPostForm
from flask_login import login_required, current_user
from app import db

blog = Blueprint('blog', __name__)

@blog.route('/blog')
def index():
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('blog/index.html', posts=posts)

@blog.route('/blog/post/<int:post_id>')
def view_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog/view_post.html', post=post)

@blog.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        # Validate that we have at least some content blocks
        content_blocks = form.get_content_blocks()
        
        # Check if any block has meaningful content (strip HTML tags for validation)
        import re
        has_content = False
        for block in content_blocks:
            content = block.get('content', '')
            # Strip HTML tags and check if there's actual text
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            if clean_content:
                has_content = True
                break
        
        if not content_blocks or not has_content:
            flash('Please add some content to your blog post.', 'error')
            return render_template('blog/create_post.html', form=form)
        
        post = BlogPost(
            title=form.title.data,
            user_id=current_user.id
        )
        post.content_blocks = content_blocks
        db.session.add(post)
        db.session.commit()
        flash('Your post has been published!', 'success')
        return redirect(url_for('blog.view_post', post_id=post.id))
    return render_template('blog/create_post.html', form=form)

@blog.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm()
    if form.validate_on_submit():
        # Validate that we have at least some content blocks
        content_blocks = form.get_content_blocks()
        
        # Check if any block has meaningful content (strip HTML tags for validation)
        import re
        has_content = False
        for block in content_blocks:
            content = block.get('content', '')
            # Strip HTML tags and check if there's actual text
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            if clean_content:
                has_content = True
                break
        
        if not content_blocks or not has_content:
            flash('Please add some content to your blog post.', 'error')
            return render_template('blog/edit_post.html', form=form, post=post)
        
        post.title = form.title.data
        post.content_blocks = content_blocks
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('blog.view_post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.set_content_blocks(post.content_blocks)
    return render_template('blog/edit_post.html', form=form, post=post)

@blog.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('blog.index')) 