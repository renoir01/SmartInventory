"""
WSGI configuration for PythonAnywhere
This file should be set as the WSGI configuration file in PythonAnywhere
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pa_wsgi.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting PythonAnywhere WSGI configuration")

# Get the username
username = os.environ.get('USER', 'renoir0')
project_path = f'/home/{username}/SmartInventory'

# Add the project directory to the Python path
logger.info(f"Adding {project_path} to Python path")
sys.path.insert(0, project_path)

# Set environment variable to indicate we're on PythonAnywhere
os.environ['PYTHONANYWHERE_SITE'] = 'true'

# Import the Flask app
try:
    logger.info("Importing app from app module")
    from app import app as application
    logger.info("Successfully imported Flask application")
except Exception as e:
    logger.error(f"Failed to import Flask application: {str(e)}")
    raise

# Log successful configuration
logger.info("WSGI configuration completed successfully")
