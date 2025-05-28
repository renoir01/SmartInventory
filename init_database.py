import sqlite3
import os
import hashlib
from datetime import datetime
import sys

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
        print(f"Database file {DB_PATH} not found, creating new database")

def hash_password(password):
    """Create a password hash"""
    # Simple hash for demonstration purposes
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_database():
    """Initialize the database with all necessary tables and users"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create user table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')
        
        # Check if product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        product_table_exists = cursor.fetchone() is not None
        
        if product_table_exists:
            # Check if the is_packaged column exists
            try:
                cursor.execute("SELECT is_packaged FROM product LIMIT 1")
                print("is_packaged column already exists in product table")
            except sqlite3.OperationalError:
                # Add missing columns to the product table
                print("Adding missing columns to product table...")
                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN is_packaged BOOLEAN DEFAULT 0")
                    print("Added is_packaged column")
                except sqlite3.OperationalError as e:
                    print(f"Error adding is_packaged column: {e}")
                
                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN units_per_package INTEGER DEFAULT 1")
                    print("Added units_per_package column")
                except sqlite3.OperationalError as e:
                    print(f"Error adding units_per_package column: {e}")
                
                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN individual_price REAL DEFAULT 0")
                    print("Added individual_price column")
                except sqlite3.OperationalError as e:
                    print(f"Error adding individual_price column: {e}")
                
                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN individual_stock INTEGER DEFAULT 0")
                    print("Added individual_stock column")
                except sqlite3.OperationalError as e:
                    print(f"Error adding individual_stock column: {e}")
        else:
            # Create product table with all required columns
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'Uncategorized',
                purchase_price REAL DEFAULT 0,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                low_stock_threshold INTEGER DEFAULT 10,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_packaged BOOLEAN DEFAULT 0,
                units_per_package INTEGER DEFAULT 1,
                individual_price REAL DEFAULT 0,
                individual_stock INTEGER DEFAULT 0
            )
            ''')
            print("Created product table with all required columns")
        
        # Create sale table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            cashier_id INTEGER NOT NULL,
            date_sold TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES product (id),
            FOREIGN KEY (cashier_id) REFERENCES user (id)
        )
        ''')
        
        # Create monthly_profit table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_profit (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            total_revenue REAL DEFAULT 0.0,
            total_cost REAL DEFAULT 0.0,
            total_profit REAL DEFAULT 0.0,
            sale_count INTEGER DEFAULT 0,
            UNIQUE(year, month)
        )
        ''')
        
        # Create cashout_record table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cashout_record (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            total_amount REAL NOT NULL,
            transaction_count INTEGER NOT NULL,
            cashed_out_by INTEGER NOT NULL,
            cashed_out_at TIMESTAMP NOT NULL,
            notes TEXT,
            FOREIGN KEY(cashed_out_by) REFERENCES user(id)
        )
        ''')
        
        # Create index on cashout_record date
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cashout_date ON cashout_record (date)')
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM user WHERE username = 'admin'")
        if not cursor.fetchone():
            # Create admin user
            cursor.execute(
                "INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                ('admin', hash_password('admin123'), 'admin')
            )
            print("Created admin user with username: admin and password: admin123")
        
        # Check if cashier user exists
        cursor.execute("SELECT id FROM user WHERE username = 'cashier'")
        if not cursor.fetchone():
            # Create cashier user
            cursor.execute(
                "INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                ('cashier', hash_password('cashier123'), 'cashier')
            )
            print("Created cashier user with username: cashier and password: cashier123")
        
        # Check if renoir01 admin user exists
        cursor.execute("SELECT id FROM user WHERE username = 'renoir01'")
        if not cursor.fetchone():
            # Create renoir01 admin user
            cursor.execute(
                "INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                ('renoir01', hash_password('admin123'), 'admin')
            )
            print("Created admin user with username: renoir01 and password: admin123")
        
        # Check if epi cashier user exists
        cursor.execute("SELECT id FROM user WHERE username = 'epi'")
        if not cursor.fetchone():
            # Create epi cashier user
            cursor.execute(
                "INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                ('epi', hash_password('cashier123'), 'cashier')
            )
            print("Created cashier user with username: epi and password: cashier123")
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error initializing database: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting database initialization...")
    backup_database()
    initialize_database()
    print("Database initialization completed")
