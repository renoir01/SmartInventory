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
                
                # If it's a product or sale table, show some sample data
                if table_name.lower() in ['product', 'sale', 'monthly_profit'] and count > 0:
                    try:
                        if table_name.lower() == 'product':
                            cursor.execute(f"SELECT id, name, price, stock FROM {table_name} LIMIT 5")
                            samples = cursor.fetchall()
                            print(f"  Sample products:")
                            for sample in samples:
                                print(f"    ID: {sample[0]}, Name: {sample[1]}, Price: {sample[2]}, Stock: {sample[3]}")
                        
                        elif table_name.lower() == 'sale':
                            cursor.execute(f"SELECT id, product_id, quantity, total_price, date_sold FROM {table_name} ORDER BY date_sold DESC LIMIT 5")
                            samples = cursor.fetchall()
                            print(f"  Recent sales:")
                            for sample in samples:
                                print(f"    ID: {sample[0]}, Product ID: {sample[1]}, Quantity: {sample[2]}, Total: {sample[3]}, Date: {sample[4]}")
                        
                        elif table_name.lower() == 'monthly_profit':
                            cursor.execute(f"SELECT id, year, month, total_revenue, total_profit FROM {table_name} ORDER BY year DESC, month DESC LIMIT 5")
                            samples = cursor.fetchall()
                            print(f"  Recent monthly profits:")
                            for sample in samples:
                                print(f"    ID: {sample[0]}, Year: {sample[1]}, Month: {sample[2]}, Revenue: {sample[3]}, Profit: {sample[4]}")
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
    # Check the May 27 backup database
    db_file = "new_inventory_backup_20250527_214054.db"
    
    print("Checking May 27 Backup Database")
    print("===============================")
    
    if os.path.exists(db_file):
        check_database_file(db_file)
    else:
        print(f"\nFile {db_file} not found, skipping...")
    
    print("\nDatabase check completed!")

if __name__ == "__main__":
    main()
