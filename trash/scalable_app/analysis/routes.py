from flask import render_template

def register_routes(bp):
    """
    Register routes for the scalable_app Blueprint.
    """

    @bp.route('/analysis')
    def analysis():
        """Render the analysis page."""
        return render_template('analysis/analysis.html')

    @bp.route('/results')
    def results():
        """Render the results page."""
        return render_template('analysis/results.html')