from flask import Blueprint, flash, redirect, url_for, request, jsonify
from app import db
from app.models.mailing_list import MailingList
from app.forms.subscription_form import SubscriptionForm

# Create subscription blueprint
subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Handle email subscription requests"""
    form = SubscriptionForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower()
        
        # Check if already subscribed but inactive
        existing = MailingList.query.filter_by(email=email).first()
        if existing and not existing.is_active:
            existing.is_active = True
            db.session.commit()
            flash('You have been resubscribed to our newsletter!', 'success')
        elif not existing:
            # Create new subscription
            subscriber = MailingList(email=email)
            db.session.add(subscriber)
            db.session.commit()
            flash('Thank you for subscribing to our newsletter!', 'success')
        else:
            flash('This email is already subscribed to our newsletter.', 'info')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'error')
                
    # Get the referrer URL or default to home page
    next_page = request.referrer or url_for('dashboard.index')
    return redirect(next_page) 