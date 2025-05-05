from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.qa import Question, Answer
from app.forms.qa import QuestionForm, AnswerForm
from app import db
from datetime import datetime
from app.utils.decorators import admin_required, subscriber_required

qa = Blueprint('qa', __name__)

@qa.route('/qa')
def index():
    page = request.args.get('page', 1, type=int)
    questions = Question.query.order_by(Question.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('qa/index.html', questions=questions)

@qa.route('/qa/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to post an answer.', 'error')
            return redirect(url_for('auth.login'))
            
        if not current_user.is_admin:
            flash('Only administrators can answer questions.', 'error')
            return redirect(url_for('qa.view_question', question_id=question.id))
        answer = Answer(
            content=form.content.data,
            user_id=current_user.id,
            question_id=question.id
        )
        db.session.add(answer)
        db.session.commit()
        flash('Your answer has been posted!', 'success')
        return redirect(url_for('qa.view_question', question_id=question.id))
        
    return render_template('qa/view_question.html', question=question, form=form)

@qa.route('/qa/ask', methods=['GET', 'POST'])
@login_required
@subscriber_required
def ask_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id
        )
        db.session.add(question)
        db.session.commit()
        flash('Your question has been posted!', 'success')
        return redirect(url_for('qa.view_question', question_id=question.id))
    return render_template('qa/ask_question.html', form=form)

@qa.route('/qa/delete/<int:question_id>', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question has been deleted!', 'success')
    return redirect(url_for('qa.index')) 