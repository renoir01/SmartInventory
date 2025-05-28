import os
import sqlite3

def check_db_file(db_path):
    """Check the structure of a database file"""
    print(f"\nChecking database file: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"  File does not exist")
        return
    
    print(f"  File size: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"  Tables: {table_names}")
        
        # Check product table if it exists
        if 'product' in table_names:
            cursor.execute("PRAGMA table_info(product)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            print(f"  Product table columns: {column_names}")
            
            # Check if there's any data in the product table
            cursor.execute("SELECT COUNT(*) FROM product")
            count = cursor.fetchone()[0]
            print(f"  Product count: {count}")
        
        conn.close()
    except Exception as e:
        print(f"  Error inspecting database: {e}")

# Check the main database files
print("Checking database files:")
check_db_file('inventory.db')
check_db_file('new_inventory.db')

# Check if the application is using the correct database file
print("\nChecking app.py for database configuration:")
try:
    with open('app.py', 'r') as f:
        for line in f:
            if 'SQLALCHEMY_DATABASE_URI' in line:
                print(f"Database URI in app.py: {line.strip()}")
except Exception as e:
    print(f"Error reading app.py: {e}")

# Suggest a solution
print("\nPossible solutions:")
print("1. Make sure the application is using the correct database file")
print("2. If using 'inventory.db', make sure it has the correct schema")
print("3. If using 'new_inventory.db', update the configuration to point to it")
