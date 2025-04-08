#!/usr/bin/env python3
"""
Deployment troubleshooting script for Smart Inventory System
This script helps diagnose and fix common deployment issues
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
        logging.FileHandler("deployment_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deployment_fix")

# Path to the database file - adjust as needed for your deployment environment
DB_PATH = 'instance/inventory.db'
PROD_DB_PATH = '/home/renoir0/SmartInventory/instance/inventory.db'

def check_environment():
    """Check the environment configuration"""
    logger.info("Checking environment configuration...")
    
    # Check Python version
    python_version = sys.version
    logger.info(f"Python version: {python_version}")
    
    # Check environment variables
    flask_app = os.environ.get('FLASK_APP')
    logger.info(f"FLASK_APP: {flask_app}")
    
    # Check current directory
    current_dir = os.getcwd()
    logger.info(f"Current directory: {current_dir}")
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    logger.info(f"Running in virtual environment: {in_venv}")
    
    return True

def check_database(db_path):
    """Check database structure and fix if needed"""
    logger.info(f"Checking database at {db_path}...")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        logger.info(f"Found tables: {', '.join(table_names)}")
        
        # Check product table structure
        if 'product' in table_names:
            cursor.execute("PRAGMA table_info(product)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            logger.info(f"Product table columns: {', '.join(column_names)}")
            
            # Check for purchase_price column
            if 'purchase_price' not in column_names:
                logger.warning("purchase_price column missing from product table. Adding it now...")
                cursor.execute("ALTER TABLE product ADD COLUMN purchase_price FLOAT DEFAULT 0")
                conn.commit()
                logger.info("Added purchase_price column to product table")
        else:
            logger.error("Product table not found in database")
            return False
        
        # Check for other required tables
        required_tables = ['user', 'sale']
        for table in required_tables:
            if table not in table_names:
                logger.error(f"Required table '{table}' not found in database")
                return False
        
        conn.close()
        logger.info("Database check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
        return False

def check_translation_files():
    """Check if translation files are properly compiled"""
    logger.info("Checking translation files...")
    
    locale_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale')
    
    if not os.path.exists(locale_dir):
        logger.error(f"Locale directory not found at {locale_dir}")
        return False
    
    # Check for .po and .mo files
    po_files = []
    mo_files = []
    
    for root, dirs, files in os.walk(locale_dir):
        for file in files:
            if file.endswith('.po'):
                po_files.append(os.path.join(root, file))
            elif file.endswith('.mo'):
                mo_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(po_files)} .po files and {len(mo_files)} .mo files")
    
    # Check if each .po file has a corresponding .mo file
    missing_mo = []
    for po_file in po_files:
        mo_file = po_file.replace('.po', '.mo')
        if mo_file not in mo_files:
            missing_mo.append(po_file)
    
    if missing_mo:
        logger.warning(f"Missing .mo files for: {', '.join(missing_mo)}")
        logger.info("Try running compile_messages.py to generate missing .mo files")
        return False
    
    logger.info("Translation files check completed successfully")
    return True

def run_diagnostics():
    """Run all diagnostic checks"""
    logger.info("Starting deployment diagnostics...")
    
    checks = [
        ("Environment", check_environment()),
        ("Local Database", check_database(DB_PATH)),
        ("Production Database", check_database(PROD_DB_PATH) if os.path.exists(PROD_DB_PATH) else None),
        ("Translation Files", check_translation_files())
    ]
    
    # Print summary
    logger.info("\n--- Diagnostic Summary ---")
    for name, result in checks:
        status = "PASS" if result else "FAIL" if result is not None else "SKIPPED"
        logger.info(f"{name}: {status}")
    
    # Provide recommendations
    logger.info("\n--- Recommendations ---")
    for name, result in checks:
        if result is False:
            if name == "Local Database" or name == "Production Database":
                logger.info("- Run migrate_db.py to fix database schema issues")
            elif name == "Translation Files":
                logger.info("- Run compile_messages.py to generate missing .mo files")
    
    logger.info("Diagnostics completed")

if __name__ == "__main__":
    run_diagnostics()
