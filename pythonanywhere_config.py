"""
Configuration file for PythonAnywhere deployment
This file contains specific settings for the PythonAnywhere environment
"""

import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pythonanywhere.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PythonAnywhere specific configuration
def get_pythonanywhere_config():
    """
    Returns configuration specific to PythonAnywhere environment
    """
    # Get username from environment or use default
    username = os.environ.get('USER', 'renoir0')
    
    # Set absolute paths for database and other files
    project_path = f'/home/{username}/SmartInventory'
    db_path = os.path.join(project_path, 'inventory.db')
    
    # Ensure the database directory exists
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")
    
    # Log the database path being used
    logger.info(f"Using database path: {db_path}")
    
    # Return configuration dictionary
    return {
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'PROJECT_PATH': project_path,
        'DB_PATH': db_path
    }
