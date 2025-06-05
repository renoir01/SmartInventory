"""
Database schema fix script for PythonAnywhere
This script checks and updates the database schema to ensure all required columns exist
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_schema.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_and_fix_schema():
    """Check and fix the database schema"""
    try:
        # Get username from environment or use default
        username = os.environ.get('USER', 'renoir0')
        
        # Define paths
        project_path = f'/home/{username}/SmartInventory'
        db_path = os.path.join(project_path, 'inventory.db')
        
        logger.info(f"Checking database at: {db_path}")
        
        # Check if database exists
        if not os.path.exists(db_path):
            logger.error(f"Database not found at: {db_path}")
            return False
        
        # Create backup before making any changes
        backup_path = f"{db_path}.backup_{int(datetime.now().timestamp())}"
        logger.info(f"Creating backup at: {backup_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Backup database
        with open(backup_path, 'wb') as f_out:
            for data in conn.iterdump():
                f_out.write(f'{data}\n'.encode('utf8'))
        
        logger.info("Database backup completed")
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            logger.error("User table does not exist!")
            # Create user table
            logger.info("Creating user table")
            cursor.execute('''
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')
            conn.commit()
            logger.info("User table created")
        else:
            logger.info("User table exists, checking columns")
            
            # Get columns in user table
            cursor.execute("PRAGMA table_info(user)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            logger.info(f"Existing columns: {column_names}")
            
            # Check if password_hash column exists
            if 'password_hash' not in column_names:
                logger.info("Adding password_hash column")
                cursor.execute("ALTER TABLE user ADD COLUMN password_hash TEXT")
                conn.commit()
                logger.info("Added password_hash column")
            
            # Check if role column exists
            if 'role' not in column_names:
                logger.info("Adding role column")
                cursor.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'user'")
                conn.commit()
                logger.info("Added role column")
        
        # Check if any users exist
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Add default admin user if no users exist
            logger.info("No users found, adding default admin")
            # Password is 'admin'
            cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)", 
                          ('admin', 'pbkdf2:sha256:600000$5QRRxLhCVPrYNo6w$e7a4f1a9d0a80a3c8be0cb81c69cc8fd7ae17f9bf8332a27a65e3bef4caa789c', 'admin'))
            conn.commit()
            logger.info("Added default admin user")
        
        # Close connection
        conn.close()
        
        logger.info("Database schema check and fix completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing database schema: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database schema fix")
    success = check_and_fix_schema()
    if success:
        logger.info("Database schema fix completed successfully")
    else:
        logger.error("Database schema fix failed")
