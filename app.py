import os
import logging
from datetime import datetime

from flask import Flask, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///disaster_risk.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'danger'

# Initialize data (for in-memory storage)
with app.app_context():
    # Import models here to avoid circular imports
    from models import User, EvacuationCenter, Evacuee, Family, Donation, InventoryItem
    
    # Create all tables
    db.create_all()
    
    # Function to load user for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Access control middleware
    @app.before_request
    def check_user_role():
        from flask import request
        
        # Skip authentication for auth routes and static files
        if (request.endpoint and 
            (request.endpoint.startswith('auth.') or 
             request.endpoint.startswith('static') or 
             request.endpoint == 'common.index')):
            return None
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            # Admin can access all routes
            if current_user.role == 'admin':
                return None
                
            # Volunteer can access volunteer routes and some common routes
            if current_user.role == 'volunteer':
                if (request.endpoint and 
                    (request.endpoint.startswith('volunteer.') or 
                     request.endpoint.startswith('common.'))):
                    return None
                else:
                    flash('You do not have permission to access this page', 'danger')
                    return redirect(url_for('volunteer.dashboard'))
                    
            # Donor can access donor routes and some common routes
            if current_user.role == 'donor':
                if (request.endpoint and 
                    (request.endpoint.startswith('donor.') or 
                     request.endpoint.startswith('common.'))):
                    return None
                else:
                    flash('You do not have permission to access this page', 'danger')
                    return redirect(url_for('donor.dashboard'))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.volunteer import volunteer_bp
    from routes.donor import donor_bp
    from routes.common import common_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(volunteer_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(common_bp)
    
    # Create admin user if it doesn't exist (for testing purposes)
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            first_name='Admin',
            last_name='User',
            is_active=True,
            created_at=datetime.now()
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info('Admin user created')
