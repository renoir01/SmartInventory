import sqlite3
import os
import sys
from datetime import datetime

def check_database_file(db_path):
    """Check the contents of a database file and print summary information"""
    try:
        if not os.path.exists(db_path):
            print(f"Error: File {db_path} does not exist")
            return False
            
        print(f"\n===== Checking database: {db_path} =====")
        print(f"File size: {os.path.getsize(db_path) / 1024:.2f} KB")
        print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
        
        # Try to connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database")
            conn.close()
            return False
            
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")
            
            # Get record count for each table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  Records: {count}")
                
                # If it's a product table with a significant number of records, this could be our target
                if table_name.lower() == 'product' and count > 100:
                    print(f"  !!! FOUND POTENTIAL MATCH: {count} products !!!")
                
                # If it's a product or sale table, show some sample data
                if table_name.lower() in ['product', 'sale', 'monthly_profit'] and count > 0:
                    try:
                        if table_name.lower() == 'product':
                            # Get column names
                            cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = [column[1] for column in cursor.fetchall()]
                            print(f"  Product table columns: {columns}")
                            
                            # Show total count
                            print(f"  Total products: {count}")
                            
                            if count > 0:
                                # Adjust query based on available columns
                                if all(col in columns for col in ['id', 'name', 'price', 'stock']):
                                    cursor.execute(f"SELECT id, name, price, stock FROM {table_name} LIMIT 5")
                                    samples = cursor.fetchall()
                                    print(f"  Sample products:")
                                    for sample in samples:
                                        print(f"    ID: {sample[0]}, Name: {sample[1]}, Price: {sample[2]}, Stock: {sample[3]}")
                                else:
                                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                                    samples = cursor.fetchall()
                                    print(f"  Sample products (raw data):")
                                    for sample in samples:
                                        print(f"    {sample}")
                                
                                if count > 5:
                                    print(f"    ... and {count - 5} more products")
                        
                        elif table_name.lower() == 'sale':
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            total_count = cursor.fetchone()[0]
                            print(f"  Total sales: {total_count}")
                            
                            if total_count > 0:
                                try:
                                    cursor.execute(f"SELECT id, product_id, quantity, total_price, date_sold FROM {table_name} ORDER BY id DESC LIMIT 5")
                                    samples = cursor.fetchall()
                                    print(f"  Recent sales:")
                                    for sample in samples:
                                        print(f"    ID: {sample[0]}, Product ID: {sample[1]}, Quantity: {sample[2]}, Total: {sample[3]}, Date: {sample[4]}")
                                except:
                                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                                    samples = cursor.fetchall()
                                    print(f"  Sample sales (raw data):")
                                    for sample in samples:
                                        print(f"    {sample}")
                                
                                if total_count > 5:
                                    print(f"    ... and {total_count - 5} more sales")
                        
                        elif table_name.lower() == 'monthly_profit':
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            total_count = cursor.fetchone()[0]
                            print(f"  Total monthly profit records: {total_count}")
                            
                            if total_count > 0:
                                try:
                                    cursor.execute(f"SELECT id, year, month, total_revenue, total_profit FROM {table_name} ORDER BY id DESC LIMIT 5")
                                    samples = cursor.fetchall()
                                    print(f"  Recent monthly profits:")
                                    for sample in samples:
                                        print(f"    ID: {sample[0]}, Year: {sample[1]}, Month: {sample[2]}, Revenue: {sample[3]}, Profit: {sample[4]}")
                                except:
                                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                                    samples = cursor.fetchall()
                                    print(f"  Sample monthly profits (raw data):")
                                    for sample in samples:
                                        print(f"    {sample}")
                                
                                if total_count > 5:
                                    print(f"    ... and {total_count - 5} more records")
                    except sqlite3.OperationalError as e:
                        print(f"  Error retrieving sample data: {str(e)}")
            except sqlite3.OperationalError as e:
                print(f"  Error counting records: {str(e)}")
        
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"SQLite error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        return False

def main():
    # List of database files to check
    db_files = [
        r"c:\Users\user\Videos\SmartInventory\inventory.db",
        r"c:\Users\user\Videos\SmartInventory\new_inventory.db",
        r"c:\Users\user\Videos\SmartInventory\new_inventory.db.old",
        r"c:\Users\user\Videos\SmartInventory\new_inventory.db.backup_20250408_185759",
        r"c:\Users\user\Videos\SmartInventory\inventory.db.backup_20250528_111358",
        r"c:\Users\user\Videos\stock_management\new_inventory.db.old",
        r"c:\Users\user\Videos\stock_management\new_inventory.db.backup_20250408_185759"
    ]
    
    # Also check if there's an inventory.db file in stock_management
    stock_db = r"c:\Users\user\Videos\stock_management\inventory.db"
    if os.path.exists(stock_db):
        db_files.append(stock_db)
    
    print("SmartInventory Database Search Tool")
    print("==================================")
    print("Searching for a database with 180+ products...")
    
    found_match = False
    
    for db_file in db_files:
        if os.path.exists(db_file):
            result = check_database_file(db_file)
            if result:
                # Check if this was a potential match
                if "FOUND POTENTIAL MATCH" in globals().get('output', ''):
                    found_match = True
        else:
            print(f"\nFile {db_file} not found, skipping...")
    
    if not found_match:
        print("\nNo database with 180+ products found in the checked files.")
        print("Consider checking other locations or contacting PythonAnywhere support.")
    
    print("\nDatabase search completed!")

if __name__ == "__main__":
    main()
