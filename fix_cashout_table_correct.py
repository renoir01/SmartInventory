import os
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_cashout_table.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_cashout_table():
    """Create the cashout_record table with the correct structure"""
    try:
        print("Creating cashout_record table...")
        
        # Connect to the database in the instance folder
        conn = sqlite3.connect('instance/inventory.db')
        cursor = conn.cursor()
        
        # Check if the cashout_record table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout_record'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("Backing up existing cashout_record table...")
            # Create a backup of the existing table if it exists
            cursor.execute("ALTER TABLE cashout_record RENAME TO cashout_record_backup")
        
        # Create the cashout_record table with the correct structure
        print("Creating new cashout_record table...")
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
        
        # Create an index on the date field
        cursor.execute("CREATE INDEX idx_cashout_record_date ON cashout_record (date)")
        
        # If we had a backup, restore the data
        if table_exists:
            print("Restoring data from backup table...")
            cursor.execute("""
            INSERT INTO cashout_record (id, date, total_amount, transaction_count, cashed_out_by, cashed_out_at, notes)
            SELECT id, date, total_amount, transaction_count, cashed_out_by, cashed_out_at, notes
            FROM cashout_record_backup
            """)
            
            # Check how many records were transferred
            cursor.execute("SELECT COUNT(*) FROM cashout_record")
            record_count = cursor.fetchone()[0]
            print(f"Restored {record_count} records from backup")
        
        conn.commit()
        print("Cashout table created/fixed successfully!")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating cashout table: {str(e)}")
        print(f"Error creating cashout table: {str(e)}")
        return False

if __name__ == "__main__":
    create_cashout_table()
    print("Done! The cashout_record table has been created/fixed.")
