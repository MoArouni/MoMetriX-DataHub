from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models.tool import Tool
from app.forms.tool_forms import ToolCreationForm, ToolConfigurationForm
from app.services.data_tool_factory import DataToolFactory

# Create blueprint
tools_bp = Blueprint('tools', __name__, url_prefix='/tools')

@tools_bp.route('/')
@login_required
def index():
    """List all user's tools"""
    user_tools = Tool.query.filter_by(creator_id=current_user.id).all()
    return render_template('tools/index.html', tools=user_tools)
    
@tools_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new tool"""
    form = ToolCreationForm()
    
    if form.validate_on_submit():
        tool = Tool(
            name=form.name.data,
            description=form.description.data,
            is_public=form.is_public.data,
            creator_id=current_user.id,
            company_id=current_user.company_id
        )
        db.session.add(tool)
        db.session.commit()
        flash('Tool created successfully!', 'success')
        return redirect(url_for('tools.configure', tool_id=tool.id))
        
    return render_template('tools/create.html', form=form)
    
@tools_bp.route('/<int:tool_id>')
@login_required
def view(tool_id):
    """View a specific tool"""
    tool = Tool.query.get_or_404(tool_id)
    
    # Check if user has permission to view this tool
    if tool.creator_id != current_user.id and (
            tool.company_id != current_user.company_id or not tool.is_public):
        flash('You do not have permission to view this tool.', 'error')
        return redirect(url_for('tools.index'))
        
    return render_template('tools/view.html', tool=tool)
    
@tools_bp.route('/<int:tool_id>/configure', methods=['GET', 'POST'])
@login_required
def configure(tool_id):
    """Configure a tool"""
    tool = Tool.query.get_or_404(tool_id)
    
    # Check if user has permission to configure this tool
    if tool.creator_id != current_user.id:
        flash('You do not have permission to configure this tool.', 'error')
        return redirect(url_for('tools.index'))
        
    form = ToolConfigurationForm()
    
    # If the tool has existing configuration, load it
    if tool.config and request.method == 'GET':
        form.from_json(tool.config)
        
    if form.validate_on_submit():
        tool.config = form.to_json()
        db.session.commit()
        flash('Tool configuration saved!', 'success')
        return redirect(url_for('tools.view', tool_id=tool.id))
        
    return render_template('tools/configure.html', form=form, tool=tool)
    
@tools_bp.route('/<int:tool_id>/delete', methods=['POST'])
@login_required
def delete(tool_id):
    """Delete a tool"""
    tool = Tool.query.get_or_404(tool_id)
    
    # Check if user has permission to delete this tool
    if tool.creator_id != current_user.id:
        flash('You do not have permission to delete this tool.', 'error')
        return redirect(url_for('tools.index'))
        
    db.session.delete(tool)
    db.session.commit()
    flash('Tool deleted successfully!', 'success')
    return redirect(url_for('tools.index')) 