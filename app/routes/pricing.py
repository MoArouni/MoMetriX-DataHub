from flask import Blueprint, render_template
from flask_login import current_user

pricing = Blueprint('pricing', __name__)

@pricing.route('/pricing')
def index():
    plans = [
        {
            'name': 'Free',
            'price': '0',
            'features': [
                'Basic data analysis',
                'Limited API access',
                'Community support',
                'Basic visualization tools'
            ],
            'recommended': False
        },
        {
            'name': 'Pro',
            'price': '29',
            'features': [
                'Advanced data analysis',
                'Full API access',
                'Priority support',
                'Advanced visualization tools',
                'Custom reports',
                'Team collaboration'
            ],
            'recommended': True
        },
        {
            'name': 'Enterprise',
            'price': '99',
            'features': [
                'Everything in Pro',
                'Dedicated support',
                'Custom solutions',
                'SLA guarantee',
                'Advanced security',
                'Training sessions'
            ],
            'recommended': False
        }
    ]
    return render_template('pricing/index.html', plans=plans) 