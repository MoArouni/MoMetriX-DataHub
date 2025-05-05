from flask import render_template

def register_routes(bp):
    """
    Register routes for the scalable_app Blueprint.
    """

    @bp.route('/login')
    def login():
        """Render the auth page."""
        return render_template('auth/login.html')

    @bp.route('/signup')
    def signup():
        """Render the auth page."""
        return render_template('auth/signup.html')