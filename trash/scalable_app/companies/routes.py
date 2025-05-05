from flask import render_template

def register_routes(bp):
    """
    Register routes for the scalable_app Blueprint.
    """

    @bp.route('/role_management')
    def role_management():
        """Render the role management page."""
        return render_template('companies/role_management.html')

    @bp.route('/dashboard')
    def dashboard():
        """Render the dashboard page."""
        return render_template('companies/dashboard.html')

    @bp.route('/create_company')
    def create_company():
        """Render the create company page."""
        return render_template('companies/create_company.html')
