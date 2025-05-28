import sqlite3
import os
from datetime import datetime

# Path to the database file
db_path = 'inventory.db'

def backup_database():
    """Create a backup of the database before making changes"""
    backup_path = f'inventory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    if os.path.exists(db_path):
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Database backup created at {backup_path}")
    else:
        print("No database file found to backup")

def fix_cashout_table():
    """Fix the cashout_record table to allow multiple cashouts per day"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing cashout records
        cursor.execute("SELECT id, date, total_amount, transaction_count, cashed_out_by, cashed_out_at, notes FROM cashout_record")
        existing_records = cursor.fetchall()
        
        # Drop the existing table
        cursor.execute("DROP TABLE IF EXISTS cashout_record")
        
        # Create the table with the new schema (without unique constraint on date)
        cursor.execute("""
        CREATE TABLE cashout_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_amount FLOAT NOT NULL DEFAULT 0.0,
            transaction_count INTEGER NOT NULL DEFAULT 0,
            cashed_out_by INTEGER NOT NULL,
            cashed_out_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (cashed_out_by) REFERENCES user (id)
        )
        """)
        
        # Create an index on the date field (but not unique)
        cursor.execute("CREATE INDEX idx_cashout_record_date ON cashout_record (date)")
        
        # Restore the existing records
        for record in existing_records:
            cursor.execute("""
            INSERT INTO cashout_record (id, date, total_amount, transaction_count, cashed_out_by, cashed_out_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, record)
        
        conn.commit()
        print("Cashout table fixed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing cashout table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database fix for cashout table...")
    backup_database()
    fix_cashout_table()
    print("Database fix completed")
