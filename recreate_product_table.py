import sqlite3
import os
import sys
from datetime import datetime

# Path to the database
DB_PATH = 'inventory.db'

def backup_database():
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f'inventory_backup_{timestamp}.db'
    
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Database backup created: {backup_path}")
    else:
        print(f"Database file {DB_PATH} not found")
        sys.exit(1)

def recreate_product_table():
    """Recreate the product table with the correct schema"""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print("Product table doesn't exist in the database")
            return False
        
        # Save any existing product data
        cursor.execute("SELECT * FROM product")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} products in the database")
        
        # Get column names
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Current product table columns: {column_names}")
        
        # Drop the product table
        cursor.execute("DROP TABLE IF EXISTS product")
        print("Dropped the existing product table")
        
        # Create a new product table with the correct schema
        cursor.execute("""
        CREATE TABLE product (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'Uncategorized',
            purchase_price REAL DEFAULT 0,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 10,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_packaged BOOLEAN DEFAULT 0,
            units_per_package INTEGER DEFAULT 1,
            individual_price REAL DEFAULT 0,
            individual_stock INTEGER DEFAULT 0
        )
        """)
        print("Created new product table with correct schema")
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(product)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        print(f"New product table columns: {new_column_names}")
        
        # Restore data if possible
        if rows and len(rows) > 0:
            # Map old data to new schema
            common_columns = [col for col in column_names if col in new_column_names]
            if common_columns:
                for row in rows:
                    # Create a dict of column values from the old data
                    row_data = dict(zip(column_names, row))
                    
                    # Extract values for common columns
                    values = [row_data.get(col) for col in common_columns]
                    placeholders = ', '.join(['?'] * len(common_columns))
                    columns_str = ', '.join(common_columns)
                    
                    # Insert into new table
                    cursor.execute(f"INSERT INTO product ({columns_str}) VALUES ({placeholders})", values)
                
                print(f"Restored {len(rows)} products to the new table")
            else:
                print("Could not restore data - no common columns")
        
        conn.commit()
        print("Product table has been successfully recreated")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error recreating product table: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting product table recreation...")
    backup_database()
    success = recreate_product_table()
    if success:
        print("Product table recreation completed successfully")
    else:
        print("Failed to recreate product table")
        sys.exit(1)
