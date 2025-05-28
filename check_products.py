import sqlite3
import os

# Path to the database
DB_PATH = 'inventory.db'

def check_products():
    """Check if there are any products in the database"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print("Product table doesn't exist in the database")
            return
        
        # Get all products
        cursor.execute("SELECT * FROM product")
        products = cursor.fetchall()
        
        if not products:
            print("No products found in the database")
            return
        
        print(f"Found {len(products)} products:")
        
        # Get column names
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Columns: {column_names}")
        
        # Print product details
        for product in products:
            print("-" * 50)
            for i, col_name in enumerate(column_names):
                if i < len(product):
                    print(f"{col_name}: {product[i]}")
        
    except Exception as e:
        print(f"Error checking products: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Checking products in database...")
    check_products()
