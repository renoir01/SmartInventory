"""
Fix script for PythonAnywhere database path issues
This script will ensure the database path is correct and accessible
"""

import os
import sys
import sqlite3
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_pythonanywhere_db.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_db_path():
    """Fix the database path on PythonAnywhere"""
    try:
        # Get username from environment or use default
        username = os.environ.get('USER', 'renoir0')
        
        # Define paths
        project_path = f'/home/{username}/SmartInventory'
        instance_path = os.path.join(project_path, 'instance')
        db_path = os.path.join(project_path, 'inventory.db')
        instance_db_path = os.path.join(instance_path, 'inventory.db')
        
        logger.info(f"Project path: {project_path}")
        logger.info(f"Instance path: {instance_path}")
        logger.info(f"Root DB path: {db_path}")
        logger.info(f"Instance DB path: {instance_db_path}")
        
        # Create instance directory if it doesn't exist
        if not os.path.exists(instance_path):
            logger.info(f"Creating instance directory: {instance_path}")
            os.makedirs(instance_path, exist_ok=True)
        
        # Check if database exists in root directory
        if os.path.exists(db_path):
            logger.info(f"Found database at root: {db_path}")
            
            # Check if we need to copy it to instance directory
            if not os.path.exists(instance_db_path):
                logger.info(f"Copying database from {db_path} to {instance_db_path}")
                shutil.copy2(db_path, instance_db_path)
                logger.info("Database copied successfully")
            else:
                # Check which is newer
                root_mtime = os.path.getmtime(db_path)
                instance_mtime = os.path.getmtime(instance_db_path)
                
                if root_mtime > instance_mtime:
                    # Root is newer, backup instance and copy root to instance
                    backup_path = f"{instance_db_path}.backup_{int(datetime.now().timestamp())}"
                    logger.info(f"Root DB is newer. Backing up instance DB to {backup_path}")
                    shutil.copy2(instance_db_path, backup_path)
                    logger.info(f"Copying newer database from {db_path} to {instance_db_path}")
                    shutil.copy2(db_path, instance_db_path)
                else:
                    # Instance is newer or same age
                    logger.info("Instance DB is current. No copy needed.")
        elif os.path.exists(instance_db_path):
            # Database only exists in instance directory, copy to root
            logger.info(f"Found database in instance directory: {instance_db_path}")
            logger.info(f"Copying database from {instance_db_path} to {db_path}")
            shutil.copy2(instance_db_path, db_path)
        else:
            # No database found
            logger.error("No database found in either location!")
            return False
        
        # Test database connections
        try:
            logger.info(f"Testing connection to root DB: {db_path}")
            conn = sqlite3.connect(db_path)
            conn.close()
            logger.info("Root DB connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to root DB: {str(e)}")
        
        try:
            logger.info(f"Testing connection to instance DB: {instance_db_path}")
            conn = sqlite3.connect(instance_db_path)
            conn.close()
            logger.info("Instance DB connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to instance DB: {str(e)}")
        
        # Set permissions to ensure both are readable/writable
        try:
            logger.info("Setting permissions on database files")
            os.chmod(db_path, 0o666)
            os.chmod(instance_db_path, 0o666)
            logger.info("Permissions set successfully")
        except Exception as e:
            logger.error(f"Failed to set permissions: {str(e)}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error fixing database path: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database path fix")
    success = fix_db_path()
    if success:
        logger.info("Database path fix completed successfully")
    else:
        logger.error("Database path fix failed")
