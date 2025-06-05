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
        post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id
        )
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
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('blog.view_post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('blog/edit_post.html', form=form, post=post)

@blog.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('blog.index')) 