import sqlite3
import os
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

def fix_database():
    """Fix the database schema to allow multiple cashouts per day"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if the cashout_record table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout_record'")
        if not cursor.fetchone():
            print("Cashout record table doesn't exist in the database")
            return
        
        # Get the current schema of the table
        cursor.execute("PRAGMA table_info(cashout_record)")
        columns = cursor.fetchall()
        print(f"Current table schema: {columns}")
        
        # Get existing data
        cursor.execute("SELECT * FROM cashout_record")
        records = cursor.fetchall()
        print(f"Found {len(records)} existing cashout records")
        
        # Create a temporary table with the correct schema
        cursor.execute("""
        CREATE TABLE temp_cashout_record (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            total_amount FLOAT NOT NULL,
            transaction_count INTEGER NOT NULL,
            cashed_out_by INTEGER NOT NULL,
            cashed_out_at DATETIME NOT NULL,
            notes TEXT,
            FOREIGN KEY(cashed_out_by) REFERENCES user(id)
        )
        """)
        
        # Copy data to the temporary table
        for record in records:
            # Ensure we have the right number of fields
            if len(record) >= 7:  # Adjust based on your actual schema
                cursor.execute("""
                INSERT INTO temp_cashout_record 
                (id, date, total_amount, transaction_count, cashed_out_by, cashed_out_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, record[:7])  # Take the first 7 fields
        
        # Drop the original table
        cursor.execute("DROP TABLE cashout_record")
        
        # Rename the temporary table
        cursor.execute("ALTER TABLE temp_cashout_record RENAME TO cashout_record")
        
        # Create an index on the date field (not unique)
        cursor.execute("CREATE INDEX idx_cashout_date ON cashout_record (date)")
        
        conn.commit()
        print("Database schema fixed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database fix...")
    backup_database()
    fix_database()
    print("Database fix completed")
