#!/usr/bin/env python
"""
Debug Fix Script for Smart Inventory System
This script creates a minimal app.py with debug logging to identify the error
"""
import os
import sys
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("debug_fix")

def fix_app_py():
    """Fix app.py with minimal code and extensive debug logging"""
    logger.info("Creating minimal app.py with debug logging...")
    
    app_path = 'app.py'
    backup_path = f"{app_path}.debug_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create backup
        if os.path.exists(app_path):
            shutil.copy2(app_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Write a minimal version with extensive debug logging
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write("""import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configure very detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
    handlers=[
        logging.FileHandler("debug_app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting application initialization")

# Initialize Flask app with minimal configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info("Flask app initialized")

# Initialize SQLAlchemy
db = SQLAlchemy(app)
logger.info("SQLAlchemy initialized")

# Initialize LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
logger.info("LoginManager initialized")

# Simple translation function
def _(text):
    return text

logger.info("Defining database models")

# Minimal User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

logger.info("User model defined")

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user with ID: {user_id}")
    try:
        user = User.query.get(int(user_id))
        if user:
            logger.debug(f"User found: {user.username}")
        else:
            logger.debug("User not found")
        return user
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

# Minimal routes
@app.route('/')
def index():
    logger.debug("Index route accessed")
    try:
        return render_template('debug.html', message="Debug mode active")
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return f"Debug mode: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug(f"Login route accessed, method: {request.method}")
    try:
        # Clear session to prevent redirect loops
        session.clear()
        logger.debug("Session cleared")
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            logger.debug(f"Login attempt for username: {username}")
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                logger.debug(f"User {username} logged in successfully")
                return redirect(url_for('index'))
            else:
                logger.debug(f"Login failed for username: {username}")
                flash(_('Invalid username or password'), 'danger')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return f"Login error: {str(e)}", 500

@app.route('/debug-info')
def debug_info():
    """Route to display debug information"""
    try:
        info = {
            'Python Version': sys.version,
            'Flask Version': Flask.__version__,
            'SQLAlchemy Version': db.Model.metadata.bind.dialect.driver,
            'Database URI': app.config['SQLALCHEMY_DATABASE_URI'],
            'Tables': [table for table in db.metadata.tables.keys()],
            'User Count': User.query.count() if db.engine.has_table('user') else 'Table not found'
        }
        return render_template('debug.html', info=info)
    except Exception as e:
        logger.error(f"Error in debug_info route: {str(e)}")
        return f"Debug info error: {str(e)}", 500

# Create a simple debug template
@app.route('/create-debug-template')
def create_debug_template():
    try:
        with open('templates/debug.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Debug Mode</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .debug-info { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1>Smart Inventory System - Debug Mode</h1>
    
    {% if message %}
    <div class="debug-info">
        <h2>Message:</h2>
        <p>{{ message }}</p>
    </div>
    {% endif %}
    
    {% if info %}
    <div class="debug-info">
        <h2>System Information:</h2>
        <ul>
            {% for key, value in info.items() %}
            <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <div class="debug-info">
        <h2>Actions:</h2>
        <ul>
            <li><a href="{{ url_for('index') }}">Home</a></li>
            <li><a href="{{ url_for('login') }}">Login</a></li>
            <li><a href="{{ url_for('debug_info') }}">System Info</a></li>
        </ul>
    </div>
</body>
</html>''')
        logger.info("Debug template created")
        return "Debug template created", 200
    except Exception as e:
        logger.error(f"Error creating debug template: {str(e)}")
        return f"Error creating debug template: {str(e)}", 500

# Initialize the database
@app.before_first_request
def initialize_database():
    logger.info("Initializing database")
    try:
        db.create_all()
        logger.info("Database tables created")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='renoir01').first()
        if not admin:
            admin = User(username='renoir01', role='admin')
            admin.set_password('Renoir@654')
            db.session.add(admin)
            logger.info("Admin user created")
        
        # Check if cashier user exists
        cashier = User.query.filter_by(username='epi').first()
        if not cashier:
            cashier = User(username='epi', role='cashier')
            cashier.set_password('Epi@654')
            db.session.add(cashier)
            logger.info("Cashier user created")
        
        db.session.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

if __name__ == '__main__':
    logger.info("Starting Flask development server")
    app.run(debug=True)
""")
        
        logger.info("Successfully created debug app.py")
        return True
    
    except Exception as e:
        logger.error(f"Error creating debug app.py: {e}")
        return False

if __name__ == "__main__":
    print("Running debug fix script for Smart Inventory System...")
    
    if fix_app_py():
        print("\nDebug fix script completed successfully!")
        print("\nInstructions:")
        print("1. Reload your web app from the PythonAnywhere Web tab")
        print("2. Access your site to trigger the error")
        print("3. Check the error logs in the PythonAnywhere Files tab")
        print("4. Look for the file 'debug_app.log' which will contain detailed error information")
        print("\nThis script creates a minimal version of your app with extensive logging")
        print("to help identify the exact cause of the Internal Server Error.")
    else:
        print("\nDebug fix script failed. Please check the logs for details.")
