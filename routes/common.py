from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

common_bp = Blueprint('common', __name__)

@common_bp.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'volunteer':
            return redirect(url_for('volunteer.dashboard'))
        else:  # donor
            return redirect(url_for('donor.dashboard'))
    
    return render_template('index.html')
