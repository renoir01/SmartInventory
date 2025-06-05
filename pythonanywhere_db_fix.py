import os
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pythonanywhere_db_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_database_path():
    """Fix the database path in app.py for PythonAnywhere deployment"""
    try:
        print("Fixing database path for PythonAnywhere...")
        
        # Read the app.py file
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Create a backup before making changes
        backup_filename = f"app.py.pythonanywhere_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_filename, 'w', encoding='utf-8') as backup_file:
            backup_file.write(content)
        
        print(f"Created backup at {backup_filename}")
        
        # Replace the database URI with a relative path that works on PythonAnywhere
        fixed_content = content.replace(
            "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/inventory.db'",
            "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'"
        )
        
        # Write the fixed content
        with open('app.py', 'w', encoding='utf-8') as file:
            file.write(fixed_content)
        
        print("Fixed database path successfully!")
        return True
    except Exception as e:
        logger.error(f"Error fixing database path: {str(e)}")
        print(f"Error fixing database path: {str(e)}")
        return False

def ensure_cashout_table_exists():
    """Create the cashout_record table if it doesn't exist"""
    try:
        print("Checking if cashout_record table exists...")
        
        # Connect to the database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Check if the cashout_record table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout_record'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("Creating cashout_record table...")
            
            # Create the cashout_record table
            cursor.execute("""
            CREATE TABLE cashout_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_amount FLOAT NOT NULL DEFAULT 0.0,
                transaction_count INTEGER NOT NULL DEFAULT 0,
                cashed_out_by INTEGER NOT NULL,
                cashed_out_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (cashed_out_by) REFERENCES user (id)
            )
            """)
            
            # Create an index on the date field
            cursor.execute("CREATE INDEX idx_cashout_record_date ON cashout_record (date)")
            
            conn.commit()
            print("Created cashout_record table successfully!")
        else:
            print("cashout_record table already exists.")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error ensuring cashout table exists: {str(e)}")
        print(f"Error ensuring cashout table exists: {str(e)}")
        return False

def initialize_database():
    """Initialize the database with required tables if they don't exist"""
    try:
        print("Initializing database...")
        
        # Connect to the database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Check if the user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        user_table_exists = cursor.fetchone() is not None
        
        if not user_table_exists:
            print("Creating user table...")
            
            # Create the user table
            cursor.execute("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                role VARCHAR(10) NOT NULL
            )
            """)
            
            # Create admin user
            from werkzeug.security import generate_password_hash
            admin_password_hash = generate_password_hash('admin')
            cursor.execute("""
            INSERT INTO user (username, password_hash, role)
            VALUES (?, ?, ?)
            """, ('admin', admin_password_hash, 'admin'))
            
            # Create cashier user
            cashier_password_hash = generate_password_hash('cashier')
            cursor.execute("""
            INSERT INTO user (username, password_hash, role)
            VALUES (?, ?, ?)
            """, ('cashier', cashier_password_hash, 'cashier'))
            
            conn.commit()
            print("Created user table with admin and cashier users.")
        
        # Check for other tables and create them if needed
        tables_to_check = ['product', 'sale', 'monthly_profit']
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone() is None:
                print(f"Table {table} is missing. Please run the full database initialization.")
        
        conn.close()
        print("Database initialization check completed.")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        print(f"Error initializing database: {str(e)}")
        return False

def main():
    print("Starting PythonAnywhere database fixes...")
    
    # Fix the database path in app.py
    db_path_fixed = fix_database_path()
    
    # Ensure the cashout_record table exists
    cashout_table_fixed = ensure_cashout_table_exists()
    
    # Initialize the database if needed
    db_initialized = initialize_database()
    
    print("\nFix Summary:")
    print(f"- Database Path: {'Fixed' if db_path_fixed else 'Error'}")
    print(f"- Cashout Table: {'Fixed' if cashout_table_fixed else 'Error'}")
    print(f"- Database Initialization: {'Completed' if db_initialized else 'Error'}")
    print("\nNOTE: You need to restart the web application on PythonAnywhere for these changes to take effect.")
    print("To restart: Go to the Web tab on PythonAnywhere and click the 'Reload' button for your web app.")

if __name__ == "__main__":
    main()
