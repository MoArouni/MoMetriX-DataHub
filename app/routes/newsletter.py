from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import re
from app import db, mail
from app.models.newsletter import NewsletterSubscriber, NewsletterCampaign
from app.utils.decorators import admin_required
from app.forms.newsletter import NewsletterCampaignForm, NewsletterSubscribeForm

newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')

# Admin routes - Main dashboard
@newsletter_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Newsletter admin dashboard"""
    
    # Statistics
    total_subscribers = NewsletterSubscriber.query.filter_by(is_active=True).count()
    total_campaigns = NewsletterCampaign.query.count()
    recent_campaigns = NewsletterCampaign.query.order_by(desc(NewsletterCampaign.created_at)).limit(5).all()
    
    # Recent subscribers (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_subscribers_30d = NewsletterSubscriber.query.filter(
        NewsletterSubscriber.subscribed_at >= thirty_days_ago
    ).count()
    
    return render_template('newsletter/admin/dashboard.html',
                         total_subscribers=total_subscribers,
                         total_campaigns=total_campaigns,
                         recent_campaigns=recent_campaigns,
                         new_subscribers_30d=new_subscribers_30d)

# Subscriber management
@newsletter_bp.route('/admin/subscribers')
@login_required
@admin_required
def admin_subscribers():
    """Manage newsletter subscribers"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', 'all', type=str)
    
    query = NewsletterSubscriber.query
    
    if search:
        query = query.filter(
            NewsletterSubscriber.email.contains(search) |
            NewsletterSubscriber.first_name.contains(search) |
            NewsletterSubscriber.last_name.contains(search)
        )
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    subscribers = query.order_by(desc(NewsletterSubscriber.subscribed_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('newsletter/admin/subscribers.html',
                         subscribers=subscribers,
                         search=search,
                         status=status)

@newsletter_bp.route('/admin/subscribers/add', methods=['POST'])
@login_required
@admin_required
def add_subscriber():
    """Add a new subscriber manually"""
    email = request.form.get('email', '').strip().lower()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    
    if not email:
        flash('Email is required.', 'error')
        return redirect(url_for('newsletter.admin_subscribers'))
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('newsletter.admin_subscribers'))
    
    # Check if already exists
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        if existing.is_active:
            flash(f'Email {email} is already subscribed.', 'warning')
        else:
            existing.resubscribe()
            flash(f'Email {email} has been reactivated.', 'success')
    else:
        # Create new subscriber
        subscriber = NewsletterSubscriber(
            email=email,
            first_name=first_name,
            last_name=last_name,
            source='admin'
        )
        db.session.add(subscriber)
        db.session.commit()
        flash(f'Successfully added {email} to the newsletter.', 'success')
    
    return redirect(url_for('newsletter.admin_subscribers'))

@newsletter_bp.route('/admin/subscribers/<int:subscriber_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_subscriber(subscriber_id):
    """Toggle subscriber active/inactive status"""
    subscriber = NewsletterSubscriber.query.get_or_404(subscriber_id)
    
    if subscriber.is_active:
        subscriber.unsubscribe()
        flash(f'{subscriber.email} has been unsubscribed.', 'success')
    else:
        subscriber.resubscribe()
        flash(f'{subscriber.email} has been resubscribed.', 'success')
    
    return redirect(url_for('newsletter.admin_subscribers'))

@newsletter_bp.route('/admin/subscribers/<int:subscriber_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subscriber(subscriber_id):
    """Delete a subscriber permanently"""
    subscriber = NewsletterSubscriber.query.get_or_404(subscriber_id)
    email = subscriber.email
    
    db.session.delete(subscriber)
    db.session.commit()
    
    flash(f'Subscriber {email} has been permanently deleted.', 'success')
    return redirect(url_for('newsletter.admin_subscribers'))

# Campaign management
@newsletter_bp.route('/admin/campaigns')
@login_required
@admin_required
def admin_campaigns():
    """Manage newsletter campaigns"""
    page = request.args.get('page', 1, type=int)
    
    campaigns = NewsletterCampaign.query.order_by(desc(NewsletterCampaign.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('newsletter/admin/campaigns.html', campaigns=campaigns)

@newsletter_bp.route('/admin/campaigns/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_campaign():
    """Create new newsletter campaign"""
    form = NewsletterCampaignForm()
    
    if form.validate_on_submit():
        campaign = NewsletterCampaign(
            title=form.title.data,
            subject=form.subject.data,
            content=form.content.data,
            html_content=form.html_content.data,
            created_by_id=current_user.id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Newsletter campaign created successfully!', 'success')
        return redirect(url_for('newsletter.admin_campaigns'))
    
    return render_template('newsletter/admin/create_campaign.html', form=form)

@newsletter_bp.route('/admin/campaigns/<int:campaign_id>/send', methods=['POST'])
@login_required
@admin_required
def send_campaign(campaign_id):
    """Send newsletter campaign to all active subscribers"""
    campaign = NewsletterCampaign.query.get_or_404(campaign_id)
    
    if campaign.status != 'draft':
        flash('Campaign has already been sent or is in progress.', 'error')
        return redirect(url_for('newsletter.admin_campaigns'))
    
    # Get all active subscribers
    subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()
    
    if not subscribers:
        flash('No active subscribers found.', 'warning')
        return redirect(url_for('newsletter.admin_campaigns'))
    
    # Update campaign status
    campaign.status = 'sending'
    campaign.total_recipients = len(subscribers)
    campaign.sent_at = datetime.utcnow()
    db.session.commit()
    
    # Send emails
    sent_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        try:
            # Create unsubscribe link
            unsubscribe_url = url_for('newsletter.unsubscribe', 
                                    email=subscriber.email, 
                                    _external=True)
            
            # Prepare email content
            content = campaign.content
            if campaign.html_content:
                html_content = campaign.html_content
                html_content += f'<br><br><small><a href="{unsubscribe_url}">Unsubscribe</a></small>'
            else:
                html_content = f'<div style="font-family: Arial, sans-serif; line-height: 1.6;">{content.replace(chr(10), "<br>")}</div>'
                html_content += f'<br><br><small><a href="{unsubscribe_url}">Unsubscribe</a></small>'
            
            msg = Message(
                subject=campaign.subject,
                recipients=[subscriber.email],
                html=html_content,
                body=content + f'\n\nUnsubscribe: {unsubscribe_url}',
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'mmtxhelp@gmail.com')
            )
            
            mail.send(msg)
            sent_count += 1
            
        except Exception as e:
            current_app.logger.error(f'Failed to send email to {subscriber.email}: {str(e)}')
            failed_count += 1
    
    # Update campaign statistics
    campaign.status = 'sent'
    campaign.emails_sent = sent_count
    campaign.emails_failed = failed_count
    db.session.commit()
    
    if sent_count > 0:
        flash(f'Campaign sent successfully! {sent_count} emails sent, {failed_count} failed.', 'success')
    else:
        flash('Failed to send campaign to any subscribers.', 'error')
        
    return redirect(url_for('newsletter.admin_campaigns'))

@newsletter_bp.route('/admin/quick-send', methods=['POST'])
@login_required
@admin_required
def quick_send():
    """Quick send newsletter to all subscribers"""
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()
    
    if not subject or not message:
        flash('Subject and message are required.', 'error')
        return redirect(url_for('newsletter.admin_dashboard'))
    
    # Get all active subscribers
    subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()
    
    if not subscribers:
        flash('No active subscribers found.', 'warning')
        return redirect(url_for('newsletter.admin_dashboard'))
    
    # Create a campaign record
    campaign = NewsletterCampaign(
        title=f"Quick Send: {subject}",
        subject=subject,
        content=message,
        created_by_id=current_user.id,
        status='sending',
        total_recipients=len(subscribers),
        sent_at=datetime.utcnow()
    )
    
    db.session.add(campaign)
    db.session.commit()
    
    # Send emails
    sent_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        try:
            # Create unsubscribe link
            unsubscribe_url = url_for('newsletter.unsubscribe', 
                                    email=subscriber.email, 
                                    _external=True)
            
            # Prepare email content
            html_content = f'<div style="font-family: Arial, sans-serif; line-height: 1.6;">{message.replace(chr(10), "<br>")}</div>'
            html_content += f'<br><br><small><a href="{unsubscribe_url}">Unsubscribe</a></small>'
            
            msg = Message(
                subject=subject,
                recipients=[subscriber.email],
                html=html_content,
                body=message + f'\n\nUnsubscribe: {unsubscribe_url}',
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'mmtxhelp@gmail.com')
            )
            
            mail.send(msg)
            sent_count += 1
            
        except Exception as e:
            current_app.logger.error(f'Failed to send email to {subscriber.email}: {str(e)}')
            failed_count += 1
    
    # Update campaign statistics
    campaign.status = 'sent'
    campaign.emails_sent = sent_count
    campaign.emails_failed = failed_count
    db.session.commit()
    
    if sent_count > 0:
        flash(f'Newsletter sent successfully! {sent_count} emails sent.', 'success')
        if failed_count > 0:
            flash(f'{failed_count} emails failed to send.', 'warning')
    else:
        flash('Failed to send newsletter to any subscribers.', 'error')
    
    return redirect(url_for('newsletter.admin_dashboard'))

# Public routes
@newsletter_bp.route('/unsubscribe')
def unsubscribe():
    """Unsubscribe from newsletter"""
    email = request.args.get('email', '').strip().lower()
    
    if not email:
        flash('Invalid unsubscribe link.', 'error')
        return redirect(url_for('dashboard.index'))
    
    subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
    
    if subscriber and subscriber.is_active:
        subscriber.unsubscribe()
        flash('You have been successfully unsubscribed from our newsletter.', 'success')
    else:
        flash('Email not found or already unsubscribed.', 'info')
    
    return render_template('newsletter/unsubscribed.html')

# Campaign viewing
@newsletter_bp.route('/admin/campaigns/<int:campaign_id>')
@login_required
@admin_required
def view_campaign(campaign_id):
    """View campaign details and statistics"""
    campaign = NewsletterCampaign.query.get_or_404(campaign_id)
    return render_template('newsletter/admin/view_campaign.html', campaign=campaign)

@newsletter_bp.route('/admin/campaigns/<int:campaign_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_campaign(campaign_id):
    """Delete a campaign"""
    campaign = NewsletterCampaign.query.get_or_404(campaign_id)
    
    if campaign.status == 'sending':
        flash('Cannot delete campaign while it is being sent.', 'error')
        return redirect(url_for('newsletter.admin_campaigns'))
    
    title = campaign.title
    db.session.delete(campaign)
    db.session.commit()
    
    flash(f'Campaign "{title}" has been deleted.', 'success')
    return redirect(url_for('newsletter.admin_campaigns'))



 