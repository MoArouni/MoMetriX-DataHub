from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models.user import User
from app.models.company import Company
from app.models.store import Store
from app.models.subscription import SubscriptionPlan, CompanySubscription
from app.models.user_permissions import UserPermissions
from app.models.join_request import JoinRequest, ModeratorInvite, DirectModeratorInvite
from app.forms.join_request_forms import AdminJoinRequestForm, AdminDirectInviteForm
from app.forms.company_settings_forms import CompanyDetailsForm, UserPermissionsForm, BulkUserPermissionsForm, CompanySettingsForm
from app.utils.email import send_join_request_declined_email, send_moderator_invite_email, send_direct_moderator_invite_email
from app import db
from datetime import datetime
from flask import current_app

# Create company admin blueprint
company_admin_bp = Blueprint('company_admin', __name__, url_prefix='/company-admin')

def company_admin_required(f):
    """Decorator to require company admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if user has a company and is the admin of that company
        if not current_user.company_id:
            flash('You need to be part of a company to access this page.', 'error')
            return redirect(url_for('dashboard.index'))
        
        company = Company.query.get(current_user.company_id)
        if not company or company.admin_id != current_user.id:
            flash('You need to be a company administrator to access this page.', 'error')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@company_admin_bp.route('/settings')
@login_required
@company_admin_required
def settings():
    """Company admin settings dashboard"""
    company = current_user.company
    subscription = CompanySubscription.query.filter_by(company_id=company.id).first()
    moderators = User.query.filter_by(company_id=company.id, role_company='moderator').all()
    stores = Store.query.filter_by(company_id=company.id).all()
    
    # Get subscription plan details
    plan = subscription.plan if subscription else None
    
    return render_template('company_admin/settings/index.html',
                         company=company,
                         subscription=subscription,
                         plan=plan,
                         moderators=moderators,
                         stores=stores)

@company_admin_bp.route('/settings/company-details', methods=['GET', 'POST'])
@login_required
@company_admin_required
def company_details():
    """Edit company details"""
    company = current_user.company
    form = CompanyDetailsForm()
    
    if form.validate_on_submit():
        try:
            company.company_name = form.company_name.data
            company.company_email = form.company_email.data
            company.phone = form.phone.data
            # Note: address, industry, description fields would need to be added to Company model
            
            db.session.commit()
            flash('Company details updated successfully!', 'success')
            return redirect(url_for('company_admin.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating company details: {str(e)}', 'error')
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.company_name.data = company.company_name
        form.company_email.data = company.company_email
        form.phone.data = company.phone
    
    return render_template('company_admin/settings/company_details.html', form=form, company=company)

@company_admin_bp.route('/settings/moderators')
@login_required
@company_admin_required
def manage_moderators():
    """Manage moderator permissions"""
    company = current_user.company
    moderators = User.query.filter_by(company_id=company.id, role_company='moderator').all()
    stores = Store.query.filter_by(company_id=company.id).all()
    
    # Get permissions for each moderator
    moderator_permissions = {}
    for moderator in moderators:
        permissions = UserPermissions.query.filter_by(
            user_id=moderator.id, 
            company_id=company.id
        ).first()
        moderator_permissions[moderator.id] = permissions
    
    return render_template('company_admin/settings/manage_moderators.html',
                         company=company,
                         moderators=moderators,
                         stores=stores,
                         moderator_permissions=moderator_permissions)

@company_admin_bp.route('/settings/moderator/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
@company_admin_required
def edit_moderator_permissions(user_id):
    """Edit specific moderator permissions"""
    company = current_user.company
    moderator = User.query.filter_by(id=user_id, company_id=company.id, role_company='moderator').first_or_404()
    
    # Get or create permissions
    permissions = UserPermissions.query.filter_by(
        user_id=moderator.id, 
        company_id=company.id
    ).first()
    
    if not permissions:
        permissions = UserPermissions(
            user_id=moderator.id,
            company_id=company.id
        )
        db.session.add(permissions)
    
    form = UserPermissionsForm(company_id=company.id)
    
    if form.validate_on_submit():
        try:
            # Update permissions
            permissions.allowed_store_ids = form.allowed_stores.data
            permissions.data_range_access = form.data_range_access.data
            permissions.can_view_sales = form.can_view_sales.data
            permissions.can_add_sales = form.can_add_sales.data
            permissions.can_edit_sales = form.can_edit_sales.data
            permissions.can_delete_sales = form.can_delete_sales.data
            permissions.can_view_analytics = form.can_view_analytics.data
            permissions.can_export_data = form.can_export_data.data
            permissions.can_manage_products = form.can_manage_products.data
            permissions.can_manage_stores = form.can_manage_stores.data
            
            db.session.commit()
            flash(f'Permissions updated for {moderator.first_name} {moderator.last_name}!', 'success')
            return redirect(url_for('company_admin.manage_moderators'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating permissions: {str(e)}', 'error')
    
    elif request.method == 'GET':
        # Pre-populate form
        form.user_id.data = moderator.id
        form.allowed_stores.data = permissions.allowed_store_ids
        form.data_range_access.data = permissions.data_range_access
        form.can_view_sales.data = permissions.can_view_sales
        form.can_add_sales.data = permissions.can_add_sales
        form.can_edit_sales.data = permissions.can_edit_sales
        form.can_delete_sales.data = permissions.can_delete_sales
        form.can_view_analytics.data = permissions.can_view_analytics
        form.can_export_data.data = permissions.can_export_data
        form.can_manage_products.data = permissions.can_manage_products
        form.can_manage_stores.data = permissions.can_manage_stores
    
    stores = Store.query.filter_by(company_id=company.id).all()
    
    return render_template('company_admin/settings/edit_permissions.html',
                         form=form,
                         moderator=moderator,
                         permissions=permissions,
                         stores=stores,
                         company=company)

@company_admin_bp.route('/settings/subscription')
@login_required
@company_admin_required
def subscription_info():
    """View subscription information"""
    company = current_user.company
    subscription = CompanySubscription.query.filter_by(company_id=company.id).first()
    plans = SubscriptionPlan.query.all()
    
    # Calculate usage statistics
    moderator_count = User.query.filter_by(company_id=company.id, role_company='moderator').count()
    total_users = User.query.filter_by(company_id=company.id).count()
    
    usage_stats = {
        'users': total_users,
        'moderators': moderator_count,
        'stores': Store.query.filter_by(company_id=company.id).count(),
    }
    
    return render_template('company_admin/settings/subscription.html',
                         company=company,
                         subscription=subscription,
                         plans=plans,
                         usage_stats=usage_stats)

@company_admin_bp.route('/settings/bulk-permissions', methods=['POST'])
@login_required
@company_admin_required
def bulk_update_permissions():
    """Update permissions for multiple users at once"""
    company = current_user.company
    form = BulkUserPermissionsForm(company_id=company.id)
    
    if form.validate_on_submit():
        try:
            user_ids = form.user_ids.data.split(',') if form.user_ids.data else []
            user_ids = [int(uid) for uid in user_ids if uid.strip()]
            
            for user_id in user_ids:
                # Verify user belongs to company
                user = User.query.filter_by(id=user_id, company_id=company.id, role_company='moderator').first()
                if not user:
                    continue
                
                # Get or create permissions
                permissions = UserPermissions.query.filter_by(
                    user_id=user_id, 
                    company_id=company.id
                ).first()
                
                if not permissions:
                    permissions = UserPermissions(
                        user_id=user_id,
                        company_id=company.id
                    )
                    db.session.add(permissions)
                
                # Update fields that were selected for update
                if form.data_range_access.data:
                    permissions.data_range_access = form.data_range_access.data
                
                if form.store_access_mode.data:
                    if form.store_access_mode.data == 'all':
                        permissions.allowed_store_ids = []  # Empty means all stores
                    elif form.store_access_mode.data == 'none':
                        all_stores = Store.query.filter_by(company_id=company.id).all()
                        permissions.allowed_store_ids = [-1]  # No stores
                    elif form.store_access_mode.data == 'specific':
                        permissions.allowed_store_ids = form.allowed_stores.data
                
                if form.update_view_sales.data:
                    permissions.can_view_sales = form.can_view_sales.data
                
                if form.update_add_sales.data:
                    permissions.can_add_sales = form.can_add_sales.data
                
                if form.update_analytics.data:
                    permissions.can_view_analytics = form.can_view_analytics.data
            
            db.session.commit()
            flash(f'Permissions updated for {len(user_ids)} users!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating permissions: {str(e)}', 'error')
    
    return redirect(url_for('company_admin.manage_moderators'))

@company_admin_bp.route('/join-requests')
@login_required
@company_admin_required
def join_requests():
    """Company admin page to manage join requests for their company"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'pending')
    
    # Calculate statistics for the company
    company_requests = JoinRequest.query.filter_by(company_id=current_user.company_id)
    stats = {
        'pending': company_requests.filter_by(status='pending').count(),
        'approved': company_requests.filter_by(status='approved').count(),
        'declined': company_requests.filter_by(status='declined').count(),
        'total': company_requests.count()
    }
    
    # Only show join requests for the current user's company
    query = JoinRequest.query.filter_by(company_id=current_user.company_id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    join_requests = query.order_by(JoinRequest.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('company_admin/join_requests.html', 
                         join_requests=join_requests.items, 
                         pagination=join_requests,
                         current_status=status_filter,
                         company=current_user.company,
                         stats=stats)

@company_admin_bp.route('/join-request/<int:request_id>', methods=['GET', 'POST'])
@login_required
@company_admin_required
def review_join_request(request_id):
    """Review a specific join request for the company"""
    join_request = JoinRequest.query.get_or_404(request_id)
    
    # Ensure the join request is for the current user's company
    if join_request.company_id != current_user.company_id:
        flash('You can only review join requests for your own company.', 'error')
        return redirect(url_for('company_admin.join_requests'))
    
    if not join_request.is_pending:
        flash('This join request has already been reviewed.', 'info')
        return redirect(url_for('company_admin.join_requests'))
    
    form = AdminJoinRequestForm()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'approve':
            # Get role permissions from form
            role_permissions = request.form.get('role_permissions')
            
            if not role_permissions:
                flash('Please select role permissions before approving.', 'error')
                return render_template('company_admin/review_join_request.html', 
                                     join_request=join_request, form=form)
            
            try:
                # Approve the request
                join_request.status = 'approved'
                join_request.reviewed_at = datetime.utcnow()
                join_request.reviewed_by = current_user.id
                
                # Create user directly instead of invite
                user = User(
                    email=join_request.email,
                    username=join_request.username,
                    first_name=join_request.first_name,
                    last_name=join_request.last_name,
                    role_website='viewer',
                    company_id=join_request.company_id,
                    role_company='moderator'
                )
                user.password = 'temp_password_123'  # They'll need to reset this
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Create permissions with the selected level
                permissions = UserPermissions(
                    user_id=user.id,
                    company_id=join_request.company_id
                )
                permissions.set_permission_level(role_permissions)
                db.session.add(permissions)
                db.session.commit()
                
                # Send welcome email with password reset link
                from app.utils.email import send_password_reset_email
                send_password_reset_email(user)
                
                flash(f'Join request approved! {join_request.full_name} has been added to your team and will receive a password reset email.', 'success')
                return redirect(url_for('company_admin.join_requests'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error approving request: {str(e)}', 'error')
                return render_template('company_admin/review_join_request.html', 
                                     join_request=join_request, form=form)
                
        elif action == 'decline':
            try:
                # Decline the request
                join_request.status = 'declined'
                join_request.reviewed_at = datetime.utcnow()
                join_request.reviewed_by = current_user.id
                db.session.commit()
                
                # Send decline notification
                send_join_request_declined_email(join_request)
                
                flash(f'Join request declined. {join_request.full_name} has been notified via email.', 'info')
                return redirect(url_for('company_admin.join_requests'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error declining request: {str(e)}', 'error')
                return render_template('company_admin/review_join_request.html', 
                                     join_request=join_request, form=form)
        else:
            flash('Invalid action. Please try again.', 'error')
            return render_template('company_admin/review_join_request.html', 
                                 join_request=join_request, form=form)
    
    return render_template('company_admin/review_join_request.html', 
                         join_request=join_request, form=form)

@company_admin_bp.route('/moderator-invites')
@login_required
@company_admin_required
def moderator_invites():
    """Company admin page to view moderator invites for their company"""
    page = request.args.get('page', 1, type=int)
    
    # Only show invites for the current user's company
    invites = ModeratorInvite.query.filter_by(company_id=current_user.company_id)\
                                   .order_by(ModeratorInvite.created_at.desc())\
                                   .paginate(page=page, per_page=20)
    
    return render_template('company_admin/moderator_invites.html', 
                         invites=invites.items, 
                         pagination=invites,
                         company=current_user.company)

@company_admin_bp.route('/invite-moderator', methods=['GET', 'POST'])
@login_required
@company_admin_required
def invite_moderator():
    """Company admin page to directly invite moderators"""
    form = AdminDirectInviteForm()
    
    if form.validate_on_submit():
        try:
            # Create direct invite
            invite = DirectModeratorInvite(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                company_id=current_user.company_id,
                invited_by=current_user.id,
                role_permissions=form.role_permissions.data,
                message=form.message.data
            )
            db.session.add(invite)
            db.session.commit()
            
            # Send invite email
            send_direct_moderator_invite_email(invite)
            
            flash(f'Invitation sent successfully to {invite.full_name} ({invite.email})!', 'success')
            return redirect(url_for('company_admin.direct_invites'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error sending invitation: {str(e)}', 'error')
    
    return render_template('company_admin/invite_moderator.html', form=form, company=current_user.company)

@company_admin_bp.route('/direct-invites')
@login_required
@company_admin_required
def direct_invites():
    """Company admin page to view direct moderator invites"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query for company's direct invites
    query = DirectModeratorInvite.query.filter_by(company_id=current_user.company_id)
    
    # Apply status filter
    if status_filter == 'pending':
        query = query.filter_by(is_used=False).filter(DirectModeratorInvite.expires_at > datetime.utcnow())
    elif status_filter == 'used':
        query = query.filter_by(is_used=True)
    elif status_filter == 'expired':
        query = query.filter_by(is_used=False).filter(DirectModeratorInvite.expires_at <= datetime.utcnow())
    
    # Calculate statistics
    all_invites = DirectModeratorInvite.query.filter_by(company_id=current_user.company_id)
    stats = {
        'pending': all_invites.filter_by(is_used=False).filter(DirectModeratorInvite.expires_at > datetime.utcnow()).count(),
        'used': all_invites.filter_by(is_used=True).count(),
        'expired': all_invites.filter_by(is_used=False).filter(DirectModeratorInvite.expires_at <= datetime.utcnow()).count(),
        'total': all_invites.count()
    }
    
    invites = query.order_by(DirectModeratorInvite.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('company_admin/direct_invites.html', 
                         invites=invites.items, 
                         pagination=invites,
                         current_status=status_filter,
                         stats=stats,
                         company=current_user.company) 