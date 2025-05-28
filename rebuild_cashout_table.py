import sqlite3
import os
from datetime import datetime

# Database file path
DB_FILE = 'inventory.db'

def backup_database():
    """Create a backup of the database"""
    backup_file = f'inventory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as src, open(backup_file, 'wb') as dst:
            dst.write(src.read())
        print(f"Database backup created: {backup_file}")
    else:
        print(f"Database file {DB_FILE} not found")

def rebuild_cashout_table():
    """Rebuild the cashout_record table without unique constraints"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout_record'")
        if not cursor.fetchone():
            print("Cashout record table doesn't exist. Nothing to rebuild.")
            return
        
        # Get existing data
        cursor.execute("SELECT * FROM cashout_record")
        records = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(cashout_record)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Found {len(records)} existing records with columns: {columns}")
        
        # Create a new table without the unique constraint
        cursor.execute("DROP TABLE IF EXISTS cashout_record_new")
        cursor.execute("""
        CREATE TABLE cashout_record_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_amount FLOAT NOT NULL,
            transaction_count INTEGER NOT NULL,
            cashed_out_by INTEGER NOT NULL,
            cashed_out_at DATETIME NOT NULL,
            notes TEXT,
            FOREIGN KEY(cashed_out_by) REFERENCES user(id)
        )
        """)
        
        # Copy data to the new table
        if records:
            placeholders = ', '.join(['?'] * len(columns))
            insert_sql = f"INSERT INTO cashout_record_new VALUES ({placeholders})"
            cursor.executemany(insert_sql, records)
        
        # Replace the old table with the new one
        cursor.execute("DROP TABLE cashout_record")
        cursor.execute("ALTER TABLE cashout_record_new RENAME TO cashout_record")
        
        # Create an index (but not unique) on the date field
        cursor.execute("CREATE INDEX idx_cashout_date ON cashout_record (date)")
        
        conn.commit()
        print("Cashout table rebuilt successfully without unique constraints")
        
    except Exception as e:
        conn.rollback()
        print(f"Error rebuilding table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting cashout table rebuild process...")
    backup_database()
    rebuild_cashout_table()
    print("Process completed")
