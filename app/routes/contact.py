from flask import Blueprint, render_template
from flask_login import current_user

# Create blueprint
contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/', methods=['GET'])
def index():
    """Contact page route"""
    form = ContactForm()
    
    # Pre-fill email if user is logged in
    if current_user.is_authenticated and not form.email.data:
        form.email.data = current_user.email
        form.name.data = f"{current_user.first_name} {current_user.last_name}"
    
    if form.validate_on_submit():
        # Send email to admin
        admin_email = 'mohamadarouni5@gmail.com'  # Or use from config
        send_email(
            to=admin_email,
            subject=f'Contact Form: {form.subject.data}',
            template='contact/email/new_message',
            name=form.name.data,
            email=form.email.data,
            message=form.message.data
        )
        
        flash('Your message has been sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('contact.index'))
        
    return render_template('contact/index.html', form=form) 

@contact_bp.route('/thank-you', methods=['GET'])
def thank_you():
    """Thank you page after successful form submission"""
    return render_template('contact/thank_you.html') 
