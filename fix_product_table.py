import sqlite3
import os
import sys

# Path to the database
DB_PATH = 'inventory.db'

def backup_database():
    """Create a backup of the database"""
    timestamp = os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0
    backup_path = f'inventory_backup_{int(timestamp)}.db'
    
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Database backup created: {backup_path}")
    else:
        print(f"Database file {DB_PATH} not found")
        sys.exit(1)

def fix_product_table():
    """Fix the product table schema by recreating it with all required columns"""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print("Product table doesn't exist in the database")
            return
        
        # Get the current schema of the product table
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Current product table columns: {column_names}")
        
        # Check if required columns exist
        required_columns = [
            'is_packaged', 'units_per_package', 'individual_price', 'individual_stock'
        ]
        
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if not missing_columns:
            print("All required columns exist in the product table")
            return
        
        print(f"Missing columns: {missing_columns}")
        
        # Get existing data from the product table
        cursor.execute("SELECT * FROM product")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} products in the database")
        
        # Get column names for the SELECT statement
        cursor.execute("SELECT * FROM product LIMIT 1")
        existing_column_names = [description[0] for description in cursor.description]
        
        # Create a temporary table with all required columns
        cursor.execute("""
        CREATE TABLE temp_product (
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
        
        # Copy data from the original table to the temporary table
        if rows:
            placeholders = ', '.join(['?'] * len(existing_column_names))
            insert_columns = ', '.join(existing_column_names)
            
            for row in rows:
                cursor.execute(f"INSERT INTO temp_product ({insert_columns}) VALUES ({placeholders})", row)
        
        # Drop the original table
        cursor.execute("DROP TABLE product")
        
        # Rename the temporary table
        cursor.execute("ALTER TABLE temp_product RENAME TO product")
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(product)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        print(f"New product table columns: {new_column_names}")
        
        conn.commit()
        print("Product table has been successfully fixed")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error fixing product table: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting product table fix...")
    backup_database()
    fix_product_table()
    print("Product table fix completed")
