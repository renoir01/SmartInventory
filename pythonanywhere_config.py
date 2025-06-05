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
def configure_pythonanywhere(app):
    """
    Configure the Flask app for PythonAnywhere environment
    Returns the database URI that was configured
    """
    # Get username from environment or use default
    username = os.environ.get('USER', 'renoir0')
    
    # Set absolute paths for database and other files
    project_path = f'/home/{username}/SmartInventory'
    root_db_path = os.path.join(project_path, 'inventory.db')
    
    # Also check for database in instance folder
    instance_path = os.path.join(project_path, 'instance')
    instance_db_path = os.path.join(instance_path, 'inventory.db')
    
    # Determine which database file to use
    if os.path.exists(instance_db_path):
        db_path = instance_db_path
        logger.info(f"Found existing database in instance folder: {db_path}")
    elif os.path.exists(root_db_path):
        db_path = root_db_path
        logger.info(f"Found existing database in root folder: {db_path}")
    else:
        # No existing database, prefer instance folder
        if not os.path.exists(instance_path):
            try:
                os.makedirs(instance_path)
                logger.info(f"Created instance directory: {instance_path}")
            except Exception as e:
                logger.error(f"Failed to create instance directory: {e}")
                # Fall back to root directory if instance creation fails
                db_path = root_db_path
                logger.info(f"Using root directory for database: {db_path}")
        else:
            db_path = instance_db_path
            logger.info(f"Using instance directory for database: {db_path}")
    
    # Log the database path being used
    logger.info(f"Using database path: {db_path}")
    
    # Return the database URI
    return f'sqlite:///{db_path}'
