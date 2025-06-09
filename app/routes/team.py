from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models.user import User
from app.models.company import Company
from app.models.store import Store
from app.models.user_permissions import UserPermissions
from app.models.join_request import JoinRequest, ModeratorInvite, DirectModeratorInvite
from app.forms.company_settings_forms import UserPermissionsForm
from app.utils.decorators import company_required
from app import db
from datetime import datetime
from sqlalchemy import and_

# Create team blueprint
team_bp = Blueprint('team', __name__, url_prefix='/team')

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

@team_bp.route('/')
@login_required
@company_admin_required
def index():
    """Team management dashboard"""
    company = current_user.company
    
    # Get all team members (excluding the admin)
    team_members = User.query.filter(
        and_(
            User.company_id == company.id,
            User.id != current_user.id  # Exclude the admin
        )
    ).all()
    
    # Get permissions for each team member
    member_permissions = {}
    for member in team_members:
        permissions = UserPermissions.query.filter_by(
            user_id=member.id, 
            company_id=company.id
        ).first()
        member_permissions[member.id] = permissions
    
    # Get stores for permission context
    stores = Store.query.filter_by(company_id=company.id).all()
    
    # Get pending join requests
    pending_requests = JoinRequest.query.filter_by(
        company_id=company.id,
        status='pending'
    ).count()
    
    # Get pending invites
    pending_invites = DirectModeratorInvite.query.filter_by(
        company_id=company.id,
        is_used=False
    ).filter(DirectModeratorInvite.expires_at > datetime.utcnow()).count()
    
    return render_template('team/index.html',
                         company=company,
                         team_members=team_members,
                         member_permissions=member_permissions,
                         stores=stores,
                         pending_requests=pending_requests,
                         pending_invites=pending_invites)

@team_bp.route('/member/<int:user_id>')
@login_required
@company_admin_required
def member_details(user_id):
    """View detailed information about a team member"""
    company = current_user.company
    
    # Get the team member (ensure they belong to the company and are not the admin)
    member = User.query.filter(
        and_(
            User.id == user_id,
            User.company_id == company.id,
            User.id != current_user.id  # Cannot view admin details
        )
    ).first_or_404()
    
    # Get permissions
    permissions = UserPermissions.query.filter_by(
        user_id=member.id, 
        company_id=company.id
    ).first()
    
    # Get stores for context
    stores = Store.query.filter_by(company_id=company.id).all()
    
    # Get member's activity stats (you can expand this)
    activity_stats = {
        'last_login': member.last_login,
        'member_since': member.created_at,
        'total_stores': len(stores) if permissions and not permissions.allowed_stores else 0
    }
    
    return render_template('team/member_details.html',
                         member=member,
                         permissions=permissions,
                         stores=stores,
                         company=company,
                         activity_stats=activity_stats)

@team_bp.route('/member/<int:user_id>/edit-permissions', methods=['GET', 'POST'])
@login_required
@company_admin_required
def edit_permissions(user_id):
    """Edit team member permissions"""
    company = current_user.company
    
    # Get the team member
    member = User.query.filter(
        and_(
            User.id == user_id,
            User.company_id == company.id,
            User.id != current_user.id  # Cannot edit admin permissions
        )
    ).first_or_404()
    
    # Get or create permissions
    permissions = UserPermissions.query.filter_by(
        user_id=member.id, 
        company_id=company.id
    ).first()
    
    if not permissions:
        permissions = UserPermissions(
            user_id=member.id,
            company_id=company.id
        )
        db.session.add(permissions)
    
    form = UserPermissionsForm(company_id=company.id)
    
    if form.validate_on_submit():
        try:
            # Update permissions using the 3 simple settings
            permissions.set_permissions(
                access_level=form.access_level.data,
                data_range=form.data_range.data,
                allowed_store_ids=form.allowed_stores.data
            )
            permissions.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(f'Permissions updated for {member.first_name} {member.last_name}!', 'success')
            return redirect(url_for('team.member_details', user_id=member.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating permissions: {str(e)}', 'error')
    
    elif request.method == 'GET':
        # Pre-populate form
        form.user_id.data = member.id
        form.access_level.data = permissions.access_level
        form.data_range.data = permissions.data_range
        form.allowed_stores.data = permissions.allowed_store_ids
    
    stores = Store.query.filter_by(company_id=company.id).all()
    
    return render_template('team/edit_permissions.html',
                         form=form,
                         member=member,
                         permissions=permissions,
                         stores=stores,
                         company=company)

@team_bp.route('/member/<int:user_id>/remove', methods=['POST'])
@login_required
@company_admin_required
def remove_member(user_id):
    """Remove a team member from the company"""
    company = current_user.company
    
    # Get the team member
    member = User.query.filter(
        and_(
            User.id == user_id,
            User.company_id == company.id,
            User.id != current_user.id  # Cannot remove admin
        )
    ).first_or_404()
    
    # Validation: Check if this is the last member
    total_members = User.query.filter_by(company_id=company.id).count()
    if total_members <= 1:
        flash('Cannot remove the last member of the company.', 'error')
        return redirect(url_for('team.member_details', user_id=user_id))
    
    # Additional validation: Check if member has critical data
    # You can add more validation here based on your business logic
    
    try:
        # Remove user permissions first
        permissions = UserPermissions.query.filter_by(
            user_id=member.id, 
            company_id=company.id
        ).first()
        if permissions:
            db.session.delete(permissions)
        
        # Remove user from company (set company_id to None and role_company to None)
        member.company_id = None
        member.role_company = None
        
        db.session.commit()
        
        flash(f'{member.first_name} {member.last_name} has been removed from the team.', 'success')
        return redirect(url_for('team.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing team member: {str(e)}', 'error')
        return redirect(url_for('team.member_details', user_id=user_id))

@team_bp.route('/member/<int:user_id>/change-role', methods=['POST'])
@login_required
@company_admin_required
def change_member_role(user_id):
    """Change a team member's company role"""
    company = current_user.company
    
    # Get the team member
    member = User.query.filter(
        and_(
            User.id == user_id,
            User.company_id == company.id,
            User.id != current_user.id  # Cannot change admin role
        )
    ).first_or_404()
    
    new_role = request.form.get('new_role')
    
    # Validate role
    valid_roles = ['moderator']  # Only moderator role available for team members
    if new_role not in valid_roles:
        flash('Invalid role specified.', 'error')
        return redirect(url_for('team.member_details', user_id=user_id))
    
    # Validation: Cannot promote to admin (only one admin per company)
    if new_role == 'admin':
        flash('Cannot promote team member to admin. Only one admin per company is allowed.', 'error')
        return redirect(url_for('team.member_details', user_id=user_id))
    
    try:
        member.role_company = new_role
        db.session.commit()
        
        flash(f'{member.first_name} {member.last_name}\'s role has been updated to {new_role}.', 'success')
        return redirect(url_for('team.member_details', user_id=user_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating role: {str(e)}', 'error')
        return redirect(url_for('team.member_details', user_id=user_id))

@team_bp.route('/bulk-actions', methods=['POST'])
@login_required
@company_admin_required
def bulk_actions():
    """Handle bulk actions on team members"""
    company = current_user.company
    
    action = request.form.get('action')
    member_ids = request.form.getlist('member_ids')
    
    if not member_ids:
        flash('No team members selected.', 'error')
        return redirect(url_for('team.index'))
    
    # Convert to integers and validate
    try:
        member_ids = [int(mid) for mid in member_ids]
    except ValueError:
        flash('Invalid member selection.', 'error')
        return redirect(url_for('team.index'))
    
    # Get members and validate they belong to the company
    members = User.query.filter(
        and_(
            User.id.in_(member_ids),
            User.company_id == company.id,
            User.id != current_user.id  # Exclude admin
        )
    ).all()
    
    if len(members) != len(member_ids):
        flash('Some selected members are invalid.', 'error')
        return redirect(url_for('team.index'))
    
    try:
        if action == 'update_permissions':
            # Bulk permission update
            data_range = request.form.get('bulk_data_range_access')
            
            for member in members:
                permissions = UserPermissions.query.filter_by(
                    user_id=member.id, 
                    company_id=company.id
                ).first()
                
                if not permissions:
                    permissions = UserPermissions(
                        user_id=member.id,
                        company_id=company.id
                    )
                    db.session.add(permissions)
                
                if data_range:
                    permissions.data_range_access = data_range
                    permissions.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(f'Permissions updated for {len(members)} team members.', 'success')
            
        elif action == 'remove_members':
            # Bulk removal (with validation)
            total_members = User.query.filter_by(company_id=company.id).count()
            if total_members - len(members) < 1:
                flash('Cannot remove all team members. At least one member must remain.', 'error')
                return redirect(url_for('team.index'))
            
            for member in members:
                # Remove permissions
                permissions = UserPermissions.query.filter_by(
                    user_id=member.id, 
                    company_id=company.id
                ).first()
                if permissions:
                    db.session.delete(permissions)
                
                # Remove from company
                member.company_id = None
                member.role_company = None
            
            db.session.commit()
            flash(f'{len(members)} team members have been removed.', 'success')
        
        else:
            flash('Invalid bulk action.', 'error')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error performing bulk action: {str(e)}', 'error')
    
    return redirect(url_for('team.index')) 