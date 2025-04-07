import sqlite3
import os

# Path to the database file
DB_PATH = 'instance/inventory.db'

def migrate_database():
    """Add the category column to the product table if it doesn't exist."""
    print("Starting database migration...")
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if the category column already exists
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'category' not in column_names:
            print("Adding 'category' column to the product table...")
            cursor.execute("ALTER TABLE product ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
            conn.commit()
            print("Migration successful: 'category' column added to the product table.")
        else:
            print("'category' column already exists in the product table.")
        
        return True
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
