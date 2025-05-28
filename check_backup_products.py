import sqlite3
import os

def check_database(db_path):
    """Check if there are any products in the specified database"""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print(f"Product table doesn't exist in {db_path}")
            return
        
        # Get all products
        cursor.execute("SELECT * FROM product")
        products = cursor.fetchall()
        
        if not products:
            print(f"No products found in {db_path}")
            return
        
        print(f"Found {len(products)} products in {db_path}:")
        
        # Get column names
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Columns: {column_names}")
        
        # Print first 5 product details
        for product in products[:5]:  # Limit to first 5 to avoid too much output
            print("-" * 50)
            for i, col_name in enumerate(column_names):
                if i < len(product):
                    print(f"{col_name}: {product[i]}")
        
        if len(products) > 5:
            print(f"... and {len(products) - 5} more products")
        
    except Exception as e:
        print(f"Error checking products in {db_path}: {e}")
    finally:
        if conn:
            conn.close()

# Check all database files
db_files = [
    'inventory.db',
    'new_inventory.db.backup_20250408_185759',
    'new_inventory.db.old'
]

for db_file in db_files:
    print("\n" + "="*70)
    print(f"Checking database: {db_file}")
    print("="*70)
    check_database(db_file)
