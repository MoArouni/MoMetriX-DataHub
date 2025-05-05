from flask import render_template

def register_routes(bp):
    """
    Register routes for the scalable_app Blueprint.
    """

    @bp.route('/settings')
    def settings():
        """Render the settings page."""
        return render_template('main/settings.html')

    @bp.route('/features')
    def features():
        """Render the features page."""
        return render_template('main/features.html')

    @bp.route('/getstarted')
    def getstarted():
        """Render the get started page."""
        return render_template('main/getstarted.html')

    @bp.route('/redirect')
    def redirect_page():
        """Render the redirect page."""
        return render_template('main/redirect.html')