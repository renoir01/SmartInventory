import sqlite3
import os

# Path to the database file
DB_PATH = 'instance/new_inventory.db'

def migrate_database():
    """Add necessary columns to tables if they don't exist."""
    print("Starting database migration...")
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist in product table
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Add category column if it doesn't exist
        if 'category' not in column_names:
            print("Adding 'category' column to the product table...")
            cursor.execute("ALTER TABLE product ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
            conn.commit()
            print("Migration successful: 'category' column added to the product table.")
        else:
            print("'category' column already exists in the product table.")
        
        # Add purchase_price column if it doesn't exist
        if 'purchase_price' not in column_names:
            print("Adding 'purchase_price' column to the product table...")
            cursor.execute("ALTER TABLE product ADD COLUMN purchase_price FLOAT DEFAULT 0")
            conn.commit()
            print("Migration successful: 'purchase_price' column added to the product table.")
        else:
            print("'purchase_price' column already exists in the product table.")
        
        # Check if columns already exist in sale table
        cursor.execute("PRAGMA table_info(sale)")
        sale_columns = cursor.fetchall()
        sale_column_names = [column[1] for column in sale_columns]
        
        # Add is_cashed_out column if it doesn't exist
        if 'is_cashed_out' not in sale_column_names:
            print("Adding 'is_cashed_out' column to the sale table...")
            cursor.execute("ALTER TABLE sale ADD COLUMN is_cashed_out BOOLEAN DEFAULT 0")
            conn.commit()
            print("Migration successful: 'is_cashed_out' column added to the sale table.")
        else:
            print("'is_cashed_out' column already exists in the sale table.")
        
        # Add cashout_id column if it doesn't exist
        if 'cashout_id' not in sale_column_names:
            print("Adding 'cashout_id' column to the sale table...")
            cursor.execute("ALTER TABLE sale ADD COLUMN cashout_id INTEGER")
            conn.commit()
            print("Migration successful: 'cashout_id' column added to the sale table.")
        else:
            print("'cashout_id' column already exists in the sale table.")
        
        # Check if cashout table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout'")
        if not cursor.fetchone():
            print("Creating 'cashout' table...")
            cursor.execute('''
                CREATE TABLE cashout (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cashier_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    note TEXT,
                    FOREIGN KEY (cashier_id) REFERENCES user (id),
                    FOREIGN KEY (admin_id) REFERENCES user (id)
                )
            ''')
            conn.commit()
            print("Migration successful: 'cashout' table created.")
        else:
            print("'cashout' table already exists.")
        
        return True
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("Database migration completed successfully.")
    else:
        print("Database migration failed.")
