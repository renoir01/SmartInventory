import sqlite3
import os
from datetime import datetime

def initialize_database():
    """Initialize the database with the correct schema"""
    db_path = 'inventory.db'
    
    # Create a backup of the existing database if it exists
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"Created database backup at {backup_path}")
        except Exception as e:
            print(f"Warning: Failed to create database backup: {e}")
    
    try:
        # Connect to the database (will create it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the user table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create the product table with all required columns
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            purchase_price REAL DEFAULT 0,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 5,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_packaged BOOLEAN DEFAULT 0,
            units_per_package INTEGER DEFAULT 1,
            individual_price REAL DEFAULT 0,
            individual_stock INTEGER DEFAULT 0
        )
        ''')
        
        # Create the sale table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profit REAL,
            cashier_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES product (id),
            FOREIGN KEY (cashier_id) REFERENCES user (id)
        )
        ''')
        
        # Create the monthly_profit table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_profit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            total_revenue REAL NOT NULL,
            total_profit REAL NOT NULL,
            date_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(month, year)
        )
        ''')
        
        # Create the cashout_record table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cashout_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cashier_id INTEGER,
            admin_id INTEGER,
            FOREIGN KEY (cashier_id) REFERENCES user (id),
            FOREIGN KEY (admin_id) REFERENCES user (id)
        )
        ''')
        
        # Check if admin user exists
        cursor.execute("SELECT * FROM user WHERE username = 'renoir01'")
        admin_exists = cursor.fetchone()
        
        # Add admin user if it doesn't exist
        if not admin_exists:
            from werkzeug.security import generate_password_hash
            admin_password = generate_password_hash('Renoir@654')
            cursor.execute(
                "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                ('renoir01', admin_password, 'admin')
            )
            print("Created admin user: renoir01 with password: Renoir@654")
        
        # Check if cashier user exists
        cursor.execute("SELECT * FROM user WHERE username = 'epi'")
        cashier_exists = cursor.fetchone()
        
        # Add cashier user if it doesn't exist
        if not cashier_exists:
            from werkzeug.security import generate_password_hash
            cashier_password = generate_password_hash('Epi@654')
            cursor.execute(
                "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                ('epi', cashier_password, 'cashier')
            )
            print("Created cashier user: epi with password: Epi@654")
        
        # Add sample products if the product table is empty
        cursor.execute("SELECT COUNT(*) FROM product")
        product_count = cursor.fetchone()[0]
        
        if product_count == 0:
            # Sample products
            sample_products = [
                ('Rice', 'Premium quality rice', 'Grains', 20.0, 35.0, 100, 20),
                ('Beans', 'Fresh beans', 'Grains', 15.0, 25.0, 80, 15),
                ('Sugar', 'White sugar', 'Groceries', 10.0, 18.0, 120, 30),
                ('Salt', 'Iodized salt', 'Groceries', 5.0, 8.0, 150, 40),
                ('Cooking Oil', 'Vegetable cooking oil', 'Groceries', 30.0, 45.0, 50, 10)
            ]
            
            for product in sample_products:
                cursor.execute('''
                INSERT INTO product (name, description, category, purchase_price, price, stock, low_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', product)
            
            print(f"Added {len(sample_products)} sample products")
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    print("Setting up the database for PythonAnywhere...")
    initialize_database()
