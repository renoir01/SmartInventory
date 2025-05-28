import os
import sqlite3
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Check which database files exist
print("Checking database files in current directory:")
for file in os.listdir('.'):
    if file.endswith('.db'):
        print(f"Found database file: {file} ({os.path.getsize(file)} bytes)")

# Check the database configuration in app.py
print("\nChecking database configuration in app.py:")
with open('app.py', 'r') as f:
    for line in f:
        if 'SQLALCHEMY_DATABASE_URI' in line:
            print(f"Database URI configuration: {line.strip()}")

# Try to connect to the database using SQLAlchemy
print("\nTrying to connect to the database using SQLAlchemy:")
try:
    engine = create_engine('sqlite:///inventory.db')
    inspector = inspect(engine)
    
    # Check if the product table exists
    print(f"Tables in the database: {inspector.get_table_names()}")
    
    if 'product' in inspector.get_table_names():
        # Get the columns of the product table
        columns = inspector.get_columns('product')
        print(f"Columns in the product table:")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")
    else:
        print("Product table not found in the database")
except Exception as e:
    print(f"Error connecting to the database with SQLAlchemy: {e}")

# Try to connect to the database using sqlite3
print("\nTrying to connect to the database using sqlite3:")
try:
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Check if the product table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    if cursor.fetchone():
        # Get the columns of the product table
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        print(f"Columns in the product table:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
    else:
        print("Product table not found in the database")
    
    conn.close()
except Exception as e:
    print(f"Error connecting to the database with sqlite3: {e}")

# Check if there are multiple database files that might be causing confusion
print("\nChecking for multiple database files:")
for file in os.listdir('.'):
    if file.endswith('.db'):
        try:
            conn = sqlite3.connect(file)
            cursor = conn.cursor()
            
            # Check if the product table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            print(f"Database file: {file}")
            print(f"  Tables: {table_names}")
            
            if 'product' in table_names:
                # Get the columns of the product table
                cursor.execute("PRAGMA table_info(product)")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                print(f"  Product table columns: {column_names}")
            
            conn.close()
        except Exception as e:
            print(f"Error inspecting database file {file}: {e}")
