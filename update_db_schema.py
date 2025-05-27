import sqlite3
import os
from app import app, db, Product, MonthlyProfit

def update_database_schema():
    """Update the database schema to add missing columns and tables."""
    print("Updating database schema...")
    
    # Database path
    db_path = 'new_inventory.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if packaged product columns exist in the product table
    cursor.execute("PRAGMA table_info(product)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add missing columns to the product table
    missing_columns = []
    if 'is_packaged' not in columns:
        missing_columns.append(('is_packaged', 'BOOLEAN DEFAULT 0'))
    if 'units_per_package' not in columns:
        missing_columns.append(('units_per_package', 'INTEGER DEFAULT 1'))
    if 'individual_price' not in columns:
        missing_columns.append(('individual_price', 'FLOAT DEFAULT 0'))
    if 'individual_stock' not in columns:
        missing_columns.append(('individual_stock', 'INTEGER DEFAULT 0'))
    
    # Add the missing columns
    for column_name, column_type in missing_columns:
        try:
            cursor.execute(f"ALTER TABLE product ADD COLUMN {column_name} {column_type}")
            print(f"Added column {column_name} to product table")
        except sqlite3.Error as e:
            print(f"Error adding column {column_name}: {e}")
    
    # Check if monthly_profit table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_profit'")
    if not cursor.fetchone():
        print("Creating monthly_profit table...")
        try:
            # Create the monthly_profit table
            cursor.execute('''
            CREATE TABLE monthly_profit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                total_revenue FLOAT DEFAULT 0.0,
                total_cost FLOAT DEFAULT 0.0,
                total_profit FLOAT DEFAULT 0.0,
                sale_count INTEGER DEFAULT 0,
                UNIQUE(year, month)
            )
            ''')
            print("Created monthly_profit table")
        except sqlite3.Error as e:
            print(f"Error creating monthly_profit table: {e}")
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    print("Database schema update completed.")
    return True

if __name__ == '__main__':
    with app.app_context():
        update_database_schema()
        
        # Recalculate monthly profits if the function exists
        if 'recalculate_monthly_profits' in globals():
            from app import recalculate_monthly_profits
            print("Recalculating monthly profits...")
            recalculate_monthly_profits()
        else:
            print("Monthly profit recalculation function not found. Skipping.")
        
        print("Schema update completed successfully.")
