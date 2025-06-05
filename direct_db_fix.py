"""
Direct database fix script for PythonAnywhere
This script directly modifies the database schema to match the expected model
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
        logging.FileHandler("direct_db_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_database():
    """Directly fix the database schema"""
    try:
        # Get username from environment or use default
        username = os.environ.get('USER', 'renoir0')
        
        # Define paths - check both possible locations
        project_path = f'/home/{username}/SmartInventory'
        db_path = os.path.join(project_path, 'inventory.db')
        instance_path = os.path.join(project_path, 'instance')
        instance_db_path = os.path.join(instance_path, 'inventory.db')
        
        # Determine which database file to use
        if os.path.exists(db_path):
            actual_db_path = db_path
            logger.info(f"Using database at: {db_path}")
        elif os.path.exists(instance_db_path):
            actual_db_path = instance_db_path
            logger.info(f"Using database at: {instance_db_path}")
        else:
            logger.error("No database file found!")
            return False
        
        # Create backup
        backup_path = f"{actual_db_path}.backup_{int(datetime.now().timestamp())}"
        logger.info(f"Creating backup at: {backup_path}")
        
        # Connect to database
        conn = sqlite3.connect(actual_db_path)
        cursor = conn.cursor()
        
        # Backup database
        with open(backup_path, 'wb') as f_out:
            for data in conn.iterdump():
                f_out.write(f'{data}\n'.encode('utf8'))
        
        logger.info("Database backup completed")
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        user_table_exists = cursor.fetchone() is not None
        
        if not user_table_exists:
            # Create user table from scratch
            logger.info("User table doesn't exist, creating it")
            cursor.execute('''
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')
            conn.commit()
            
            # Add default admin user
            logger.info("Adding default admin user")
            # Password is 'admin'
            cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)", 
                          ('admin', 'pbkdf2:sha256:600000$5QRRxLhCVPrYNo6w$e7a4f1a9d0a80a3c8be0cb81c69cc8fd7ae17f9bf8332a27a65e3bef4caa789c', 'admin'))
            conn.commit()
            
            logger.info("Added default admin user")
        else:
            # User table exists, check columns
            logger.info("User table exists, checking columns")
            
            # Get columns in user table
            cursor.execute("PRAGMA table_info(user)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            logger.info(f"Existing columns: {column_names}")
            
            # Check if password_hash column exists
            if 'password_hash' not in column_names:
                logger.info("Adding password_hash column")
                
                # SQLite doesn't support adding NOT NULL columns to existing tables without a default value
                # So we need to recreate the table
                
                # Create temporary table with correct schema
                logger.info("Creating temporary table with correct schema")
                cursor.execute('''
                    CREATE TABLE user_new (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL
                    )
                ''')
                
                # Copy data from old table to new table
                logger.info("Copying data from old table to new table")
                
                # Check if role column exists in old table
                if 'role' in column_names:
                    # Copy existing data with default password_hash
                    cursor.execute('''
                        INSERT INTO user_new (id, username, password_hash, role)
                        SELECT id, username, 'pbkdf2:sha256:600000$5QRRxLhCVPrYNo6w$e7a4f1a9d0a80a3c8be0cb81c69cc8fd7ae17f9bf8332a27a65e3bef4caa789c', role FROM user
                    ''')
                else:
                    # Copy existing data with default password_hash and role
                    cursor.execute('''
                        INSERT INTO user_new (id, username, password_hash, role)
                        SELECT id, username, 'pbkdf2:sha256:600000$5QRRxLhCVPrYNo6w$e7a4f1a9d0a80a3c8be0cb81c69cc8fd7ae17f9bf8332a27a65e3bef4caa789c', 'user' FROM user
                    ''')
                
                # Drop old table
                logger.info("Dropping old table")
                cursor.execute("DROP TABLE user")
                
                # Rename new table to old table name
                logger.info("Renaming new table to old table name")
                cursor.execute("ALTER TABLE user_new RENAME TO user")
                
                conn.commit()
                logger.info("User table structure fixed")
            
            # Check if role column exists
            elif 'role' not in column_names:
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
        
        # Check if other required tables exist
        required_tables = ['product', 'category', 'sale', 'sale_item', 'cashout_record']
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone() is None:
                logger.warning(f"Table '{table}' doesn't exist!")
        
        # Close connection
        conn.close()
        
        logger.info("Database fix completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting direct database fix")
    success = fix_database()
    if success:
        logger.info("Database fix completed successfully")
    else:
        logger.error("Database fix failed")
