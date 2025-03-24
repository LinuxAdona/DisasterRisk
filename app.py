import os
import logging
from datetime import datetime
from flask import Flask, session
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'danger'

# Import models to initialize in-memory data storage
from models import init_db, User, EvacuationCenter, Evacuee, Family, Donation, InventoryItem

# Initialize the database
init_db()

# Import all routes
from routes import register_routes
register_routes(app)

# Initialize session handling
@app.before_request
def before_request():
    session.permanent = True

# Template filters
@app.template_filter('format_date')
def format_date(value, format='%B %d, %Y'):
    if value:
        return value.strftime(format)
    return ""

@app.template_filter('format_datetime')
def format_datetime(value, format='%B %d, %Y %I:%M %p'):
    if value:
        return value.strftime(format)
    return ""

@app.context_processor
def inject_now():
    return {'now': datetime.now()}
