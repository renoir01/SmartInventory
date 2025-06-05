import sqlite3
import os

# Print the current directory
print(f"Current directory: {os.getcwd()}")

# Check if the database file exists
db_path = 'instance/inventory.db'
print(f"Checking if database exists at {db_path}: {os.path.exists(db_path)}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get schema for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"  Columns in {table[0]}:")
        for col in columns:
            print(f"    {col[1]} ({col[2]})")
    
    # Check specifically for CashoutRecord table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout_record'")
    if cursor.fetchone():
        print("\nCashoutRecord table exists")
        cursor.execute("SELECT * FROM cashout_record LIMIT 5")
        records = cursor.fetchall()
        print(f"Number of cashout records: {len(records)}")
    else:
        print("\nCashoutRecord table does NOT exist")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
