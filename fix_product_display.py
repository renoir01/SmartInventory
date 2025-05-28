import sqlite3
import os
import sys
import shutil
from datetime import datetime

# Path to the database
DB_PATH = 'inventory.db'

def backup_database():
    """Create a backup of the current database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup_{timestamp}"
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"Created database backup at {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to create database backup: {e}")
        return False

def fix_product_display():
    """Fix the product display functionality"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found")
        return False
    
    # Create a backup first
    if not backup_database():
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print("Product table doesn't exist in the database")
            return False
        
        # Get the current schema of the product table
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Check if the required columns exist
        required_columns = [
            'id', 'name', 'description', 'category', 'purchase_price', 
            'price', 'stock', 'low_stock_threshold', 'date_added'
        ]
        
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            print("Creating a new product table with the correct schema...")
            
            # Create a temporary table with the correct schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    purchase_price REAL DEFAULT 0,
                    price REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    low_stock_threshold INTEGER DEFAULT 5,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_packaged BOOLEAN DEFAULT 0,
                    units_per_package INTEGER DEFAULT 1,
                    individual_price REAL DEFAULT 0,
                    individual_stock INTEGER DEFAULT 0
                )
            """)
            
            # Copy data from the old table to the new one
            existing_columns = ', '.join([col for col in column_names if col in required_columns])
            new_columns = ', '.join([col for col in required_columns if col in column_names])
            
            cursor.execute(f"""
                INSERT INTO product_new ({new_columns})
                SELECT {existing_columns} FROM product
            """)
            
            # Drop the old table and rename the new one
            cursor.execute("DROP TABLE product")
            cursor.execute("ALTER TABLE product_new RENAME TO product")
            
            print("Product table has been recreated with the correct schema")
        else:
            # Check if the problematic columns exist
            problematic_columns = ['is_packaged', 'units_per_package', 'individual_price', 'individual_stock']
            missing_problematic = [col for col in problematic_columns if col not in column_names]
            
            if missing_problematic:
                print(f"Adding missing columns: {missing_problematic}")
                
                # Add the missing columns
                for col in missing_problematic:
                    if col == 'is_packaged':
                        cursor.execute("ALTER TABLE product ADD COLUMN is_packaged BOOLEAN DEFAULT 0")
                    elif col == 'units_per_package':
                        cursor.execute("ALTER TABLE product ADD COLUMN units_per_package INTEGER DEFAULT 1")
                    elif col == 'individual_price':
                        cursor.execute("ALTER TABLE product ADD COLUMN individual_price REAL DEFAULT 0")
                    elif col == 'individual_stock':
                        cursor.execute("ALTER TABLE product ADD COLUMN individual_stock INTEGER DEFAULT 0")
                
                print("Added missing columns to the product table")
            else:
                print("Product table schema is correct")
        
        # Commit the changes
        conn.commit()
        print("Database schema has been updated successfully")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Current product table columns: {column_names}")
        
        return True
    except Exception as e:
        print(f"Error fixing product display: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Fixing product display functionality...")
    if fix_product_display():
        print("Fix completed successfully")
    else:
        print("Failed to fix product display")
